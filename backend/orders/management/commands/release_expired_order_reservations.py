from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from inventory.models import BranchInventory
from orders.models import StockReservation
from orders.services import release_expired_for_inventories


class Command(BaseCommand):
    help = "Release expired ecommerce stock reservations and cancel unpaid orders."

    @transaction.atomic
    def handle(self, *args, **options):
        inventory_ids = StockReservation.objects.filter(
            status=StockReservation.Status.ACTIVE,
            expires_at__lte=timezone.now(),
        ).values_list("inventory_id", flat=True)
        inventories = list(
            BranchInventory.objects.select_for_update()
            .filter(id__in=inventory_ids)
            .order_by("id")
        )
        released = release_expired_for_inventories(inventories)
        self.stdout.write(
            self.style.SUCCESS(f"Released {released} expired reservation(s).")
        )
