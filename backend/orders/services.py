from django.db import transaction
from django.utils import timezone

from inventory.models import BranchInventory, StockMovement

from .models import Order, StockReservation


def _movement(
    inventory,
    movement_type,
    *,
    on_hand_change=0,
    reserved_change=0,
    order,
    actor=None,
    note="",
):
    StockMovement.objects.create(
        inventory=inventory,
        movement_type=movement_type,
        quantity_on_hand_change=on_hand_change,
        quantity_reserved_change=reserved_change,
        quantity_on_hand_after=inventory.quantity_on_hand,
        quantity_reserved_after=inventory.quantity_reserved,
        reference_type="order",
        reference_id=order.reference,
        note=note,
        performed_by=actor if getattr(actor, "is_authenticated", False) else None,
    )


def release_expired_for_inventories(inventories, *, now=None):
    """Release expired reservations while caller holds inventory row locks."""
    now = now or timezone.now()
    inventory_by_id = {inventory.id: inventory for inventory in inventories}
    reservations = list(
        StockReservation.objects.select_for_update()
        .select_related("order")
        .filter(
            inventory_id__in=inventory_by_id,
            status=StockReservation.Status.ACTIVE,
            expires_at__lte=now,
        )
        .order_by("inventory_id", "id")
    )
    for reservation in reservations:
        inventory = inventory_by_id[reservation.inventory_id]
        inventory.quantity_reserved = max(
            0, inventory.quantity_reserved - reservation.quantity
        )
        inventory.save(update_fields=["quantity_reserved", "updated_at"])
        reservation.status = StockReservation.Status.EXPIRED
        reservation.released_at = now
        reservation.save(update_fields=["status", "released_at", "updated_at"])
        _movement(
            inventory,
            StockMovement.MovementType.RELEASE,
            reserved_change=-reservation.quantity,
            order=reservation.order,
            note="Expired checkout stock reservation released.",
        )
    expired_order_ids = {reservation.order_id for reservation in reservations}
    for order in Order.objects.select_for_update().filter(
        id__in=expired_order_ids,
        status=Order.Status.AWAITING_PAYMENT,
    ):
        if not order.stock_reservations.filter(
            status=StockReservation.Status.ACTIVE
        ).exists():
            order.status = Order.Status.CANCELLED
            order.payment_status = "expired"
            order.cancelled_at = now
            order.save(
                update_fields=[
                    "status", "payment_status", "cancelled_at", "updated_at"
                ]
            )
    return len(reservations)


@transaction.atomic
def release_order_reservations(order, *, actor=None, reason="Order cancelled."):
    inventory_ids = list(
        StockReservation.objects.filter(
            order=order, status=StockReservation.Status.ACTIVE
        ).values_list("inventory_id", flat=True)
    )
    inventories = {
        inventory.id: inventory
        for inventory in BranchInventory.objects.select_for_update()
        .filter(id__in=inventory_ids)
        .order_by("id")
    }
    order = Order.objects.select_for_update().get(pk=order.pk)
    reservations = list(
        StockReservation.objects.select_for_update()
        .filter(order=order, status=StockReservation.Status.ACTIVE)
        .order_by("inventory_id")
    )
    now = timezone.now()
    for reservation in reservations:
        inventory = inventories[reservation.inventory_id]
        inventory.quantity_reserved -= reservation.quantity
        inventory.save(update_fields=["quantity_reserved", "updated_at"])
        reservation.status = StockReservation.Status.RELEASED
        reservation.released_at = now
        reservation.save(update_fields=["status", "released_at", "updated_at"])
        _movement(
            inventory,
            StockMovement.MovementType.RELEASE,
            reserved_change=-reservation.quantity,
            order=order,
            actor=actor,
            note=reason,
        )
    return order


@transaction.atomic
def capture_order_stock(order, *, actor=None):
    """Convert active reservations to final deductions after verified payment."""
    inventory_ids = list(
        StockReservation.objects.filter(
            order=order, status=StockReservation.Status.ACTIVE
        ).values_list("inventory_id", flat=True)
    )
    inventories = {
        inventory.id: inventory
        for inventory in BranchInventory.objects.select_for_update()
        .filter(id__in=inventory_ids)
        .order_by("id")
    }
    order = Order.objects.select_for_update().get(pk=order.pk)
    if order.status not in {
        Order.Status.AWAITING_PAYMENT,
        Order.Status.PAYMENT_UNDER_REVIEW,
    }:
        return order
    reservations = list(
        StockReservation.objects.select_for_update()
        .filter(order=order, status=StockReservation.Status.ACTIVE)
        .order_by("inventory_id")
    )
    if not reservations or any(item.expires_at <= timezone.now() for item in reservations):
        raise ValueError("The order's stock reservation has expired.")
    now = timezone.now()
    for reservation in reservations:
        inventory = inventories[reservation.inventory_id]
        if (
            inventory.quantity_reserved < reservation.quantity
            or inventory.quantity_on_hand < reservation.quantity
        ):
            raise ValueError("Reserved stock is no longer consistent.")
        inventory.quantity_reserved -= reservation.quantity
        inventory.quantity_on_hand -= reservation.quantity
        inventory.save(
            update_fields=["quantity_reserved", "quantity_on_hand", "updated_at"]
        )
        reservation.status = StockReservation.Status.CONVERTED
        reservation.converted_at = now
        reservation.save(update_fields=["status", "converted_at", "updated_at"])
        _movement(
            inventory,
            StockMovement.MovementType.SALE,
            on_hand_change=-reservation.quantity,
            reserved_change=-reservation.quantity,
            order=order,
            actor=actor,
            note="Verified order payment converted reserved stock to a sale.",
        )
    order.status = Order.Status.PAID
    order.payment_status = "paid"
    order.paid_at = now
    order.save(update_fields=["status", "payment_status", "paid_at", "updated_at"])
    return order
