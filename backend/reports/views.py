from collections import defaultdict
from datetime import date, timedelta
from decimal import Decimal

from django.db.models import Q
from django.utils import timezone
from rest_framework import serializers
from rest_framework.response import Response
from rest_framework.views import APIView

from branches.models import Branch, BranchStaffAssignment
from branches.permissions import IsOwnerOrAssignedBranchStaff, get_accessible_branch_ids
from bookings.models import Booking, BookingServiceItem
from inventory.models import BranchInventory, StockMovement
from orders.models import Order
from orders.models import OrderItem
from payments.models import Payment
from pos.models import POSPaymentEntry, POSSale, POSSaleLine
from products.models import ProductCategory
from services.models import Service
from .exports import REPORTS, export_csv, export_excel, export_pdf


FINAL_PAYMENT_CORRECTION_STATUSES = (Payment.Status.REFUNDED, Payment.Status.CANCELLED)
FINAL_POS_PAYMENT_CORRECTION_STATUSES = ("refunded", "cancelled")


def _online_payment_occurred_at(payment):
    if payment.status in FINAL_PAYMENT_CORRECTION_STATUSES:
        return payment.updated_at
    if payment.status == Payment.Status.SUCCEEDED:
        return payment.paid_at or payment.created_at
    return payment.created_at


def _pos_payment_occurred_at(entry):
    return entry.updated_at if entry.status in FINAL_POS_PAYMENT_CORRECTION_STATUSES else entry.created_at


class ManagementSalesReportView(APIView):
    """Branch-scoped online-order and POS revenue report."""

    permission_classes = [IsOwnerOrAssignedBranchStaff]
    required_branch_roles = (BranchStaffAssignment.Role.MANAGER,)

    class FilterSerializer(serializers.Serializer):
        date_from = serializers.DateField(required=False)
        date_to = serializers.DateField(required=False)
        branch = serializers.UUIDField(required=False)
        source = serializers.ChoiceField(
            choices=(("all", "All"), ("online", "Online orders"), ("pos", "POS")),
            required=False,
            default="all",
        )
        interval = serializers.ChoiceField(
            choices=(("daily", "Daily"), ("weekly", "Weekly"), ("monthly", "Monthly")),
            required=False,
            default="daily",
        )

        def validate(self, attrs):
            today = timezone.localdate()
            attrs.setdefault("date_to", today)
            attrs.setdefault("date_from", attrs["date_to"] - timedelta(days=29))
            if attrs["date_from"] > attrs["date_to"]:
                raise serializers.ValidationError({"date_to": "The end date cannot be before the start date."})
            if (attrs["date_to"] - attrs["date_from"]).days > 366:
                raise serializers.ValidationError({"date_to": "Select a reporting period of 366 days or less."})
            return attrs

    def get(self, request):
        query = self.FilterSerializer(data=request.query_params)
        query.is_valid(raise_exception=True)
        filters = query.validated_data
        branch_ids = get_accessible_branch_ids(request.user, self.required_branch_roles)
        selected_branch = filters.get("branch")
        if selected_branch and selected_branch not in branch_ids:
            raise serializers.ValidationError({"branch": "This branch is outside your reporting assignment."})
        scope = {selected_branch} if selected_branch else branch_ids
        source = filters["source"]
        date_from = filters["date_from"]
        date_to = filters["date_to"]

        online_orders = Order.objects.select_related("branch", "customer").filter(
            branch_id__in=scope,
            payment_status="paid",
            paid_at__date__range=(date_from, date_to),
        ).exclude(status__in=(Order.Status.CANCELLED, Order.Status.RETURNED, Order.Status.REFUNDED))
        pos_sales = POSSale.objects.select_related("branch", "cashier", "customer").filter(
            branch_id__in=scope,
            status=POSSale.Status.COMPLETED,
            completed_at__date__range=(date_from, date_to),
        )
        if source == "online":
            pos_sales = pos_sales.none()
        elif source == "pos":
            online_orders = online_orders.none()

        transactions = []
        daily = defaultdict(lambda: {"online": Decimal("0.00"), "pos": Decimal("0.00"), "count": 0})
        branch_totals = defaultdict(lambda: {"name": "", "online": Decimal("0.00"), "pos": Decimal("0.00"), "count": 0})
        for order in online_orders:
            occurred = order.paid_at
            amount = order.total_amount
            day = occurred.date().isoformat()
            daily[day]["online"] += amount
            daily[day]["count"] += 1
            branch_totals[str(order.branch_id)]["name"] = order.branch.name
            branch_totals[str(order.branch_id)]["online"] += amount
            branch_totals[str(order.branch_id)]["count"] += 1
            transactions.append({
                "reference": order.reference, "source": "online", "branch_name": order.branch.name,
                "customer_name": order.customer.full_name if order.customer else order.recipient_name or "Customer",
                "occurred_at": occurred, "status": order.status, "amount": f"{amount:.2f}",
            })
        for sale in pos_sales:
            occurred = sale.completed_at or sale.created_at
            amount = sale.total_amount
            day = occurred.date().isoformat()
            daily[day]["pos"] += amount
            daily[day]["count"] += 1
            branch_totals[str(sale.branch_id)]["name"] = sale.branch.name
            branch_totals[str(sale.branch_id)]["pos"] += amount
            branch_totals[str(sale.branch_id)]["count"] += 1
            transactions.append({
                "reference": sale.reference, "source": "pos", "branch_name": sale.branch.name,
                "customer_name": sale.customer.full_name if sale.customer else "Walk-in customer",
                "occurred_at": occurred, "status": sale.status, "amount": f"{amount:.2f}",
                "cashier_name": sale.cashier.full_name if sale.cashier else "Unassigned",
            })

        online_total = sum((order.total_amount for order in online_orders), Decimal("0.00"))
        pos_total = sum((sale.total_amount for sale in pos_sales), Decimal("0.00"))
        payment_methods = defaultdict(lambda: {"amount": Decimal("0.00"), "count": 0})
        if source != "pos":
            for payment in Payment.objects.filter(
                order__in=online_orders, status=Payment.Status.SUCCEEDED,
            ):
                key = payment.method or payment.provider or "electronic"
                payment_methods[key]["amount"] += payment.amount
                payment_methods[key]["count"] += 1
        if source != "online":
            for entry in POSPaymentEntry.objects.filter(sale__in=pos_sales, status="succeeded"):
                payment_methods[entry.method]["amount"] += entry.amount
                payment_methods[entry.method]["count"] += 1

        interval = filters["interval"]
        trend = defaultdict(lambda: {"online": Decimal("0.00"), "pos": Decimal("0.00"), "count": 0})
        for day, values in daily.items():
            period_date = date.fromisoformat(day)
            if interval == "weekly":
                period = period_date - timedelta(days=period_date.weekday())
            elif interval == "monthly":
                period = period_date.replace(day=1)
            else:
                period = period_date
            key = period.isoformat()
            trend[key]["online"] += values["online"]
            trend[key]["pos"] += values["pos"]
            trend[key]["count"] += values["count"]

        branches = Branch.objects.filter(pk__in=branch_ids, is_active=True).order_by("name")
        online_count = len([transaction for transaction in transactions if transaction["source"] == "online"])
        pos_count = len([transaction for transaction in transactions if transaction["source"] == "pos"])
        total_revenue = online_total + pos_total
        return Response({
            "filters": {"date_from": date_from, "date_to": date_to, "branch": str(selected_branch) if selected_branch else "", "source": source, "interval": interval},
            "branches": [{"id": str(branch.pk), "code": branch.code, "name": branch.name} for branch in branches],
            "summary": {
                "total_revenue": f"{total_revenue:.2f}", "online_revenue": f"{online_total:.2f}",
                "pos_revenue": f"{pos_total:.2f}", "transaction_count": len(transactions),
                "online_count": online_count, "pos_count": pos_count,
                "online_share_percent": f"{((online_total / total_revenue) * 100) if total_revenue else Decimal('0.00'):.2f}",
                "pos_share_percent": f"{((pos_total / total_revenue) * 100) if total_revenue else Decimal('0.00'):.2f}",
                "online_average_sale": f"{(online_total / online_count) if online_count else Decimal('0.00'):.2f}",
                "pos_average_sale": f"{(pos_total / pos_count) if pos_count else Decimal('0.00'):.2f}",
                "average_sale": f"{(total_revenue / len(transactions)) if transactions else Decimal('0.00'):.2f}",
            },
            "daily": [
                {"date": day, "online": f"{values['online']:.2f}", "pos": f"{values['pos']:.2f}", "total": f"{values['online'] + values['pos']:.2f}", "count": values["count"]}
                for day, values in sorted(daily.items())
            ],
            "trend": [
                {"period_start": period, "interval": interval, "online": f"{values['online']:.2f}", "pos": f"{values['pos']:.2f}", "total": f"{values['online'] + values['pos']:.2f}", "count": values["count"]}
                for period, values in sorted(trend.items())
            ],
            "by_branch": [
                {"branch_id": branch_id, "branch_name": values["name"], "online": f"{values['online']:.2f}", "pos": f"{values['pos']:.2f}", "total": f"{values['online'] + values['pos']:.2f}", "count": values["count"]}
                for branch_id, values in sorted(branch_totals.items(), key=lambda item: item[1]["name"])
            ],
            "payment_methods": [
                {"method": method, "amount": f"{values['amount']:.2f}", "count": values["count"]}
                for method, values in sorted(payment_methods.items())
            ],
            "transactions": sorted(transactions, key=lambda item: item["occurred_at"], reverse=True)[:500],
        })


class ManagementBookingsReportView(APIView):
    """Branch-scoped booking volume, status, source, and value report."""

    permission_classes = [IsOwnerOrAssignedBranchStaff]
    required_branch_roles = (BranchStaffAssignment.Role.MANAGER,)

    class FilterSerializer(serializers.Serializer):
        date_from = serializers.DateField(required=False)
        date_to = serializers.DateField(required=False)
        branch = serializers.UUIDField(required=False)
        status = serializers.ChoiceField(choices=Booking.Status.choices, required=False)
        source = serializers.ChoiceField(choices=Booking.Source.choices, required=False)

        def validate(self, attrs):
            today = timezone.localdate()
            attrs.setdefault("date_to", today + timedelta(days=30))
            attrs.setdefault("date_from", today - timedelta(days=29))
            if attrs["date_from"] > attrs["date_to"]:
                raise serializers.ValidationError({"date_to": "The end date cannot be before the start date."})
            if (attrs["date_to"] - attrs["date_from"]).days > 366:
                raise serializers.ValidationError({"date_to": "Select a reporting period of 366 days or less."})
            return attrs

    def get(self, request):
        query = self.FilterSerializer(data=request.query_params)
        query.is_valid(raise_exception=True)
        filters = query.validated_data
        branch_ids = get_accessible_branch_ids(request.user, self.required_branch_roles)
        selected_branch = filters.get("branch")
        if selected_branch and selected_branch not in branch_ids:
            raise serializers.ValidationError({"branch": "This branch is outside your reporting assignment."})

        scope = {selected_branch} if selected_branch else branch_ids
        bookings = Booking.objects.select_related("branch", "customer").prefetch_related("service_items").filter(
            branch_id__in=scope,
            preferred_start__date__range=(filters["date_from"], filters["date_to"]),
        )
        if filters.get("status"):
            bookings = bookings.filter(status=filters["status"])
        if filters.get("source"):
            bookings = bookings.filter(source=filters["source"])

        status_totals = defaultdict(lambda: {"count": 0, "value": Decimal("0.00")})
        source_totals = defaultdict(lambda: {"count": 0, "value": Decimal("0.00")})
        daily = defaultdict(lambda: {"count": 0, "cancelled_count": 0, "no_show_count": 0, "value": Decimal("0.00")})
        branch_totals = defaultdict(lambda: {"name": "", "count": 0, "value": Decimal("0.00")})
        rows = []
        total_value = Decimal("0.00")
        total_duration = 0
        completed_count = 0
        cancelled_count = 0
        no_show_count = 0
        rejected_count = 0

        for booking in bookings:
            value = booking.total_amount
            day = booking.preferred_start.date().isoformat()
            total_value += value
            total_duration += booking.total_duration_minutes
            completed_count += booking.status == Booking.Status.COMPLETED
            cancelled_count += booking.status == Booking.Status.CANCELLED
            no_show_count += booking.status == Booking.Status.NO_SHOW
            rejected_count += booking.status == Booking.Status.REJECTED
            status_totals[booking.status]["count"] += 1
            status_totals[booking.status]["value"] += value
            source_totals[booking.source]["count"] += 1
            source_totals[booking.source]["value"] += value
            daily[day]["count"] += 1
            daily[day]["cancelled_count"] += booking.status == Booking.Status.CANCELLED
            daily[day]["no_show_count"] += booking.status == Booking.Status.NO_SHOW
            daily[day]["value"] += value
            branch_totals[str(booking.branch_id)]["name"] = booking.branch.name
            branch_totals[str(booking.branch_id)]["count"] += 1
            branch_totals[str(booking.branch_id)]["value"] += value
            rows.append({
                "reference": booking.reference,
                "branch_name": booking.branch.name,
                "customer_name": booking.customer.full_name if booking.customer else booking.recipient_name or "Customer",
                "preferred_start": booking.preferred_start,
                "status": booking.status,
                "source": booking.source,
                "payment_status": booking.payment_status,
                "service_names": [item.service_name for item in booking.service_items.all()],
                "duration_minutes": booking.total_duration_minutes,
                "amount": f"{value:.2f}",
            })

        count = len(rows)
        active_count = count - cancelled_count - no_show_count - rejected_count
        branches = Branch.objects.filter(pk__in=branch_ids, is_active=True).order_by("name")
        return Response({
            "filters": {
                "date_from": filters["date_from"], "date_to": filters["date_to"],
                "branch": str(selected_branch) if selected_branch else "",
                "status": filters.get("status", ""), "source": filters.get("source", ""),
            },
            "branches": [{"id": str(branch.pk), "code": branch.code, "name": branch.name} for branch in branches],
            "choices": {
                "statuses": [{"value": value, "label": label} for value, label in Booking.Status.choices],
                "sources": [{"value": value, "label": label} for value, label in Booking.Source.choices],
            },
            "summary": {
                "booking_count": count, "active_count": active_count, "completed_count": completed_count,
                "cancelled_count": cancelled_count,
                "cancellation_rate": f"{((Decimal(cancelled_count) / count) * 100) if count else Decimal('0.00'):.2f}",
                "no_show_count": no_show_count,
                "no_show_rate": f"{((Decimal(no_show_count) / count) * 100) if count else Decimal('0.00'):.2f}",
                "rejected_count": rejected_count, "booked_value": f"{total_value:.2f}",
                "average_value": f"{(total_value / count) if count else Decimal('0.00'):.2f}",
                "total_duration_minutes": total_duration,
            },
            "by_status": [{"status": key, "count": values["count"], "value": f"{values['value']:.2f}"} for key, values in sorted(status_totals.items())],
            "by_source": [{"source": key, "count": values["count"], "value": f"{values['value']:.2f}"} for key, values in sorted(source_totals.items())],
            "daily": [{"date": key, "count": values["count"], "cancelled_count": values["cancelled_count"], "no_show_count": values["no_show_count"], "value": f"{values['value']:.2f}"} for key, values in sorted(daily.items())],
            "by_branch": [{"branch_id": key, "branch_name": values["name"], "count": values["count"], "value": f"{values['value']:.2f}"} for key, values in sorted(branch_totals.items(), key=lambda item: item[1]["name"])],
            "bookings": sorted(rows, key=lambda item: item["preferred_start"], reverse=True)[:500],
        })


class ManagementProductsReportView(APIView):
    """Branch-scoped product sales and current inventory report."""

    permission_classes = [IsOwnerOrAssignedBranchStaff]
    required_branch_roles = (BranchStaffAssignment.Role.MANAGER,)

    class FilterSerializer(serializers.Serializer):
        date_from = serializers.DateField(required=False)
        date_to = serializers.DateField(required=False)
        branch = serializers.UUIDField(required=False)
        source = serializers.ChoiceField(choices=(("all", "All"), ("online", "Online"), ("pos", "POS")), required=False, default="all")
        stock = serializers.ChoiceField(choices=(("all", "All"), ("low", "Low stock"), ("out", "Out of stock")), required=False, default="all")

        def validate(self, attrs):
            today = timezone.localdate()
            attrs.setdefault("date_to", today)
            attrs.setdefault("date_from", today - timedelta(days=29))
            if attrs["date_from"] > attrs["date_to"]:
                raise serializers.ValidationError({"date_to": "The end date cannot be before the start date."})
            if (attrs["date_to"] - attrs["date_from"]).days > 366:
                raise serializers.ValidationError({"date_to": "Select a reporting period of 366 days or less."})
            return attrs

    def get(self, request):
        query = self.FilterSerializer(data=request.query_params)
        query.is_valid(raise_exception=True)
        filters = query.validated_data
        branch_ids = get_accessible_branch_ids(request.user, self.required_branch_roles)
        selected_branch = filters.get("branch")
        if selected_branch and selected_branch not in branch_ids:
            raise serializers.ValidationError({"branch": "This branch is outside your reporting assignment."})
        scope = {selected_branch} if selected_branch else branch_ids

        products = defaultdict(lambda: {"name": "", "variant": "", "sku": "", "online_units": 0, "pos_units": 0, "online_revenue": Decimal("0.00"), "pos_revenue": Decimal("0.00"), "online_cost": Decimal("0.00"), "pos_cost": Decimal("0.00"), "stock_on_hand": 0, "stock_reserved": 0, "reorder_level": 0})
        if filters["source"] != "pos":
            items = OrderItem.objects.select_related("order").filter(
                order__branch_id__in=scope, order__payment_status="paid",
                order__paid_at__date__range=(filters["date_from"], filters["date_to"]),
            ).exclude(order__status__in=(Order.Status.CANCELLED, Order.Status.RETURNED, Order.Status.REFUNDED))
            for item in items:
                row = products[item.sku]
                row.update(name=item.product_name, variant=item.variant_name, sku=item.sku)
                row["online_units"] += item.quantity
                row["online_revenue"] += item.line_total
                row["online_cost"] += item.line_cost
        if filters["source"] != "online":
            lines = POSSaleLine.objects.select_related("sale").filter(
                sale__branch_id__in=scope, sale__status=POSSale.Status.COMPLETED,
                sale__completed_at__date__range=(filters["date_from"], filters["date_to"]),
                item_type=POSSaleLine.ItemType.PRODUCT,
            )
            for item in lines:
                key = item.sku or item.item_reference
                row = products[key]
                row.update(name=item.name, variant=item.option_name, sku=item.sku or item.item_reference)
                row["pos_units"] += item.quantity
                row["pos_revenue"] += item.line_total
                row["pos_cost"] += item.line_cost

        inventories = BranchInventory.objects.select_related("product_variant__product").filter(branch_id__in=scope)
        for inventory in inventories:
            variant = inventory.product_variant
            row = products[variant.sku]
            row.update(name=variant.product.name, variant=variant.name, sku=variant.sku)
            row["stock_on_hand"] += inventory.quantity_on_hand
            row["stock_reserved"] += inventory.quantity_reserved
            row["reorder_level"] += inventory.reorder_level

        rows = []
        for values in products.values():
            available = values["stock_on_hand"] - values["stock_reserved"]
            stock_state = "out" if available <= 0 else "low" if available <= values["reorder_level"] else "healthy"
            if filters["stock"] != "all" and stock_state != filters["stock"]:
                continue
            units = values["online_units"] + values["pos_units"]
            revenue = values["online_revenue"] + values["pos_revenue"]
            cost = values["online_cost"] + values["pos_cost"]
            gross_profit = revenue - cost
            rows.append({**values, "units_sold": units, "revenue": f"{revenue:.2f}", "online_revenue": f"{values['online_revenue']:.2f}", "pos_revenue": f"{values['pos_revenue']:.2f}", "cost_of_goods": f"{cost:.2f}", "gross_profit": f"{gross_profit:.2f}", "gross_margin_percent": f"{((gross_profit / revenue) * 100) if revenue else Decimal('0.00'):.2f}", "stock_available": available, "stock_state": stock_state})
        rows.sort(key=lambda row: (-Decimal(row["revenue"]), row["name"]))
        best_selling_products = sorted(
            rows,
            key=lambda row: (-row["units_sold"], -Decimal(row["revenue"]), row["name"]),
        )[:5]
        total_units = sum(row["units_sold"] for row in rows)
        total_revenue = sum((Decimal(row["revenue"]) for row in rows), Decimal("0.00"))
        total_cost = sum((Decimal(row["cost_of_goods"]) for row in rows), Decimal("0.00"))
        gross_profit = total_revenue - total_cost
        branches = Branch.objects.filter(pk__in=branch_ids, is_active=True).order_by("name")
        return Response({
            "filters": {"date_from": filters["date_from"], "date_to": filters["date_to"], "branch": str(selected_branch) if selected_branch else "", "source": filters["source"], "stock": filters["stock"]},
            "branches": [{"id": str(branch.pk), "code": branch.code, "name": branch.name} for branch in branches],
            "summary": {"product_count": len(rows), "units_sold": total_units, "revenue": f"{total_revenue:.2f}", "cost_of_goods": f"{total_cost:.2f}", "gross_profit": f"{gross_profit:.2f}", "gross_margin_percent": f"{((gross_profit / total_revenue) * 100) if total_revenue else Decimal('0.00'):.2f}", "average_unit_revenue": f"{(total_revenue / total_units) if total_units else Decimal('0.00'):.2f}", "low_stock_count": sum(row["stock_state"] == "low" for row in rows), "out_of_stock_count": sum(row["stock_state"] == "out" for row in rows)},
            "best_selling_products": [
                {
                    "rank": rank,
                    "name": row["name"],
                    "variant": row["variant"],
                    "sku": row["sku"],
                    "units_sold": row["units_sold"],
                    "revenue": row["revenue"],
                }
                for rank, row in enumerate(best_selling_products, start=1)
            ],
            "products": rows[:500],
        })


class ManagementServicesReportView(APIView):
    """Branch-scoped booked and POS service performance report."""

    permission_classes = [IsOwnerOrAssignedBranchStaff]
    required_branch_roles = (BranchStaffAssignment.Role.MANAGER,)

    class FilterSerializer(serializers.Serializer):
        date_from = serializers.DateField(required=False)
        date_to = serializers.DateField(required=False)
        branch = serializers.UUIDField(required=False)
        source = serializers.ChoiceField(choices=(("all", "All"), ("booking", "Bookings"), ("pos", "POS")), required=False, default="all")
        status = serializers.ChoiceField(choices=Booking.Status.choices, required=False)
        service = serializers.UUIDField(required=False)

        def validate(self, attrs):
            today = timezone.localdate()
            attrs.setdefault("date_to", today + timedelta(days=30))
            attrs.setdefault("date_from", today - timedelta(days=29))
            if attrs["date_from"] > attrs["date_to"]:
                raise serializers.ValidationError({"date_to": "The end date cannot be before the start date."})
            if (attrs["date_to"] - attrs["date_from"]).days > 366:
                raise serializers.ValidationError({"date_to": "Select a reporting period of 366 days or less."})
            return attrs

    def get(self, request):
        query = self.FilterSerializer(data=request.query_params)
        query.is_valid(raise_exception=True)
        filters = query.validated_data
        branch_ids = get_accessible_branch_ids(request.user, self.required_branch_roles)
        selected_branch = filters.get("branch")
        if selected_branch and selected_branch not in branch_ids:
            raise serializers.ValidationError({"branch": "This branch is outside your reporting assignment."})
        scope = {selected_branch} if selected_branch else branch_ids
        accessible_services = Service.objects.filter(branch_availability__branch_id__in=branch_ids).distinct().order_by("name")
        selected_service = filters.get("service")
        if selected_service and not accessible_services.filter(pk=selected_service).exists():
            raise serializers.ValidationError({"service": "This service is outside your reporting assignment."})

        services = defaultdict(lambda: {"id": "", "name": "", "booking_count": 0, "pos_count": 0, "booking_revenue": Decimal("0.00"), "pos_revenue": Decimal("0.00"), "duration_minutes": 0, "completed_count": 0})
        daily = defaultdict(lambda: {"booking_count": 0, "pos_count": 0, "revenue": Decimal("0.00")})
        if filters["source"] != "pos":
            booking_items = BookingServiceItem.objects.select_related("booking", "service").filter(
                booking__branch_id__in=scope,
                booking__preferred_start__date__range=(filters["date_from"], filters["date_to"]),
            )
            if filters.get("status"):
                booking_items = booking_items.filter(booking__status=filters["status"])
            if selected_service:
                booking_items = booking_items.filter(service_id=selected_service)
            for item in booking_items:
                key = str(item.service_id)
                row = services[key]
                row.update(id=key, name=item.service_name)
                row["booking_count"] += 1
                row["duration_minutes"] += item.duration_minutes
                row["completed_count"] += item.booking.status == Booking.Status.COMPLETED
                day = item.booking.preferred_start.date().isoformat()
                daily[day]["booking_count"] += 1
                # Booking revenue is recognized only after full payment and is
                # removed when the booking no longer represents a valid sale.
                if (
                    item.booking.payment_status == "paid"
                    and item.booking.status
                    not in (Booking.Status.CANCELLED, Booking.Status.REJECTED)
                ):
                    row["booking_revenue"] += item.unit_price
                    daily[day]["revenue"] += item.unit_price
        if filters["source"] != "booking" and not filters.get("status"):
            pos_lines = POSSaleLine.objects.select_related("sale").filter(
                sale__branch_id__in=scope, sale__status=POSSale.Status.COMPLETED,
                sale__completed_at__date__range=(filters["date_from"], filters["date_to"]),
                item_type=POSSaleLine.ItemType.SERVICE,
            )
            if selected_service:
                pos_lines = pos_lines.filter(item_reference=str(selected_service))
            for item in pos_lines:
                key = item.item_reference
                row = services[key]
                row.update(id=key, name=item.name)
                row["pos_count"] += item.quantity
                row["pos_revenue"] += item.line_total
                day = (item.sale.completed_at or item.sale.created_at).date().isoformat()
                daily[day]["pos_count"] += item.quantity
                daily[day]["revenue"] += item.line_total

        rows = []
        for values in services.values():
            count = values["booking_count"] + values["pos_count"]
            revenue = values["booking_revenue"] + values["pos_revenue"]
            rows.append({**values, "service_count": count, "revenue": f"{revenue:.2f}", "booking_revenue": f"{values['booking_revenue']:.2f}", "pos_revenue": f"{values['pos_revenue']:.2f}", "average_value": f"{(revenue / count) if count else Decimal('0.00'):.2f}"})
        rows.sort(key=lambda row: (-Decimal(row["revenue"]), row["name"]))
        popular_services = sorted(
            rows,
            key=lambda row: (-row["service_count"], -Decimal(row["revenue"]), row["name"]),
        )[:5]
        total_count = sum(row["service_count"] for row in rows)
        total_revenue = sum((Decimal(row["revenue"]) for row in rows), Decimal("0.00"))
        branches = Branch.objects.filter(pk__in=branch_ids, is_active=True).order_by("name")
        return Response({
            "filters": {"date_from": filters["date_from"], "date_to": filters["date_to"], "branch": str(selected_branch) if selected_branch else "", "source": filters["source"], "status": filters.get("status", ""), "service": str(selected_service) if selected_service else ""},
            "branches": [{"id": str(branch.pk), "name": branch.name} for branch in branches],
            "services": [{"id": str(service.pk), "name": service.name} for service in accessible_services],
            "statuses": [{"value": value, "label": label} for value, label in Booking.Status.choices],
            "summary": {"service_count": total_count, "distinct_services": len(rows), "revenue": f"{total_revenue:.2f}", "average_value": f"{(total_revenue / total_count) if total_count else Decimal('0.00'):.2f}", "completed_bookings": sum(row["completed_count"] for row in rows), "duration_minutes": sum(row["duration_minutes"] for row in rows)},
            "popular_services": [
                {
                    "rank": rank,
                    "id": row["id"],
                    "name": row["name"],
                    "service_count": row["service_count"],
                    "booking_count": row["booking_count"],
                    "pos_count": row["pos_count"],
                    "revenue": row["revenue"],
                }
                for rank, row in enumerate(popular_services, start=1)
            ],
            "daily": [{"date": key, "booking_count": values["booking_count"], "pos_count": values["pos_count"], "revenue": f"{values['revenue']:.2f}"} for key, values in sorted(daily.items())],
            "performance": rows[:500],
        })


class ManagementInventoryReportView(APIView):
    """Branch-scoped stock position, valuation, and movement report."""

    permission_classes = [IsOwnerOrAssignedBranchStaff]
    required_branch_roles = (BranchStaffAssignment.Role.MANAGER,)

    class FilterSerializer(serializers.Serializer):
        date_from = serializers.DateField(required=False)
        date_to = serializers.DateField(required=False)
        branch = serializers.UUIDField(required=False)
        category = serializers.UUIDField(required=False)
        stock = serializers.ChoiceField(choices=(("all", "All"), ("healthy", "Healthy"), ("low", "Low"), ("out", "Out")), required=False, default="all")
        search = serializers.CharField(required=False, allow_blank=True, max_length=100)

        def validate(self, attrs):
            today = timezone.localdate()
            attrs.setdefault("date_to", today)
            attrs.setdefault("date_from", today - timedelta(days=29))
            if attrs["date_from"] > attrs["date_to"]:
                raise serializers.ValidationError({"date_to": "The end date cannot be before the start date."})
            if (attrs["date_to"] - attrs["date_from"]).days > 366:
                raise serializers.ValidationError({"date_to": "Select a reporting period of 366 days or less."})
            return attrs

    def get(self, request):
        query = self.FilterSerializer(data=request.query_params)
        query.is_valid(raise_exception=True)
        filters = query.validated_data
        branch_ids = get_accessible_branch_ids(request.user, self.required_branch_roles)
        selected_branch = filters.get("branch")
        if selected_branch and selected_branch not in branch_ids:
            raise serializers.ValidationError({"branch": "This branch is outside your reporting assignment."})
        scope = {selected_branch} if selected_branch else branch_ids
        inventory = BranchInventory.objects.select_related("branch", "product_variant__product__category").filter(branch_id__in=scope)
        category_ids = inventory.values_list("product_variant__product__category_id", flat=True).distinct()
        categories = ProductCategory.objects.filter(pk__in=category_ids).order_by("name")
        selected_category = filters.get("category")
        if selected_category and not categories.filter(pk=selected_category).exists():
            raise serializers.ValidationError({"category": "This category is outside your reporting scope."})
        if selected_category:
            inventory = inventory.filter(product_variant__product__category_id=selected_category)
        search = filters.get("search", "").strip()
        if search:
            from django.db.models import Q
            inventory = inventory.filter(Q(product_variant__product__name__icontains=search) | Q(product_variant__sku__icontains=search) | Q(product_variant__name__icontains=search))

        inventory_rows = list(inventory)
        movement_totals = defaultdict(lambda: {"on_hand_change": 0, "reserved_change": 0, "count": 0})
        movements = list(StockMovement.objects.select_related(
            "inventory__branch", "inventory__product_variant__product", "performed_by",
        ).filter(
            inventory_id__in=[item.pk for item in inventory_rows],
            created_at__date__range=(filters["date_from"], filters["date_to"]),
        ))
        for movement in movements:
            values = movement_totals[movement.inventory_id]
            values["on_hand_change"] += movement.quantity_on_hand_change
            values["reserved_change"] += movement.quantity_reserved_change
            values["count"] += 1

        rows = []
        included_inventory_ids = set()
        for item in inventory_rows:
            variant = item.product_variant
            available = item.quantity_available
            stock_state = "out" if available <= 0 else "low" if available <= item.reorder_level else "healthy"
            if filters["stock"] != "all" and filters["stock"] != stock_state:
                continue
            included_inventory_ids.add(item.pk)
            movement = movement_totals[item.pk]
            rows.append({
                "variant_id": str(variant.pk), "branch_name": item.branch.name,
                "product_name": variant.product.name, "variant_name": variant.name,
                "category_name": variant.product.category.name, "sku": variant.sku,
                "quantity_on_hand": item.quantity_on_hand, "quantity_reserved": item.quantity_reserved,
                "quantity_available": available, "reorder_level": item.reorder_level,
                "stock_state": stock_state, "cost_value": f"{variant.cost_price * available:.2f}",
                "retail_value": f"{variant.selling_price * available:.2f}",
                "movement_count": movement["count"], "on_hand_change": movement["on_hand_change"],
                "reserved_change": movement["reserved_change"],
            })
        visible_movements = [
            movement for movement in movements
            if movement.inventory_id in included_inventory_ids
        ]
        movements_by_type = defaultdict(lambda: {"count": 0, "on_hand_change": 0, "reserved_change": 0})
        for movement in visible_movements:
            kind = movements_by_type[movement.movement_type]
            kind["on_hand_change"] += movement.quantity_on_hand_change
            kind["reserved_change"] += movement.quantity_reserved_change
            kind["count"] += 1
        rows.sort(key=lambda row: (row["branch_name"], row["product_name"], row["variant_name"]))
        branches = Branch.objects.filter(pk__in=branch_ids, is_active=True).order_by("name")
        return Response({
            "filters": {"date_from": filters["date_from"], "date_to": filters["date_to"], "branch": str(selected_branch) if selected_branch else "", "category": str(selected_category) if selected_category else "", "stock": filters["stock"], "search": search},
            "branches": [{"id": str(branch.pk), "name": branch.name} for branch in branches],
            "categories": [{"id": str(category.pk), "name": category.name} for category in categories],
            "summary": {"inventory_count": len(rows), "quantity_on_hand": sum(row["quantity_on_hand"] for row in rows), "quantity_reserved": sum(row["quantity_reserved"] for row in rows), "quantity_available": sum(row["quantity_available"] for row in rows), "cost_value": f"{sum((Decimal(row['cost_value']) for row in rows), Decimal('0.00')):.2f}", "retail_value": f"{sum((Decimal(row['retail_value']) for row in rows), Decimal('0.00')):.2f}", "low_stock_count": sum(row["stock_state"] == "low" for row in rows), "out_of_stock_count": sum(row["stock_state"] == "out" for row in rows), "movement_count": sum(row["movement_count"] for row in rows), "on_hand_change": sum(row["on_hand_change"] for row in rows)},
            "movements_by_type": [{"type": key, **values} for key, values in sorted(movements_by_type.items())],
            "movements": [
                {
                    "id": str(movement.pk),
                    "occurred_at": movement.created_at,
                    "type": movement.movement_type,
                    "branch_name": movement.inventory.branch.name,
                    "product_name": movement.inventory.product_variant.product.name,
                    "variant_name": movement.inventory.product_variant.name,
                    "sku": movement.inventory.product_variant.sku,
                    "on_hand_change": movement.quantity_on_hand_change,
                    "reserved_change": movement.quantity_reserved_change,
                    "on_hand_after": movement.quantity_on_hand_after,
                    "reserved_after": movement.quantity_reserved_after,
                    "reference_type": movement.reference_type,
                    "reference_id": movement.reference_id,
                    "note": movement.note,
                    "performed_by": movement.performed_by.full_name if movement.performed_by else "System",
                }
                for movement in visible_movements[:1000]
            ],
            "inventory": rows[:1000],
        })


class ManagementPaymentsReportView(APIView):
    """Branch-scoped online and POS payment activity report."""

    permission_classes = [IsOwnerOrAssignedBranchStaff]
    required_branch_roles = (BranchStaffAssignment.Role.MANAGER,)

    class FilterSerializer(serializers.Serializer):
        date_from = serializers.DateField(required=False)
        date_to = serializers.DateField(required=False)
        branch = serializers.UUIDField(required=False)
        source = serializers.ChoiceField(choices=(("all", "All"), ("online", "Online"), ("pos", "POS")), required=False, default="all")
        status = serializers.CharField(required=False, allow_blank=True, max_length=30)
        method = serializers.CharField(required=False, allow_blank=True, max_length=40)
        provider = serializers.CharField(required=False, allow_blank=True, max_length=40)

        def validate(self, attrs):
            today = timezone.localdate()
            attrs.setdefault("date_to", today)
            attrs.setdefault("date_from", today - timedelta(days=29))
            if attrs["date_from"] > attrs["date_to"]:
                raise serializers.ValidationError({"date_to": "The end date cannot be before the start date."})
            if (attrs["date_to"] - attrs["date_from"]).days > 366:
                raise serializers.ValidationError({"date_to": "Select a reporting period of 366 days or less."})
            return attrs

    def get(self, request):
        query = self.FilterSerializer(data=request.query_params)
        query.is_valid(raise_exception=True)
        filters = query.validated_data
        branch_ids = get_accessible_branch_ids(request.user, self.required_branch_roles)
        selected_branch = filters.get("branch")
        if selected_branch and selected_branch not in branch_ids:
            raise serializers.ValidationError({"branch": "This branch is outside your reporting assignment."})
        scope = {selected_branch} if selected_branch else branch_ids

        date_range = (filters["date_from"], filters["date_to"])
        online = Payment.objects.select_related("branch", "customer", "booking", "order").filter(
            Q(status__in=FINAL_PAYMENT_CORRECTION_STATUSES, updated_at__date__range=date_range)
            | Q(status=Payment.Status.SUCCEEDED, paid_at__date__range=date_range)
            | Q(status=Payment.Status.SUCCEEDED, paid_at__isnull=True, created_at__date__range=date_range)
            | Q(status__in=(Payment.Status.PENDING, Payment.Status.FAILED), created_at__date__range=date_range),
            branch_id__in=scope,
        )
        pos = POSPaymentEntry.objects.select_related("sale__branch", "sale__customer", "sale__cashier").filter(
            Q(status__in=FINAL_POS_PAYMENT_CORRECTION_STATUSES, updated_at__date__range=date_range)
            | Q(status__in=("succeeded", "pending", "failed"), created_at__date__range=date_range),
            sale__branch_id__in=scope,
        )
        status_filter = filters.get("status", "").strip()
        method_filter = filters.get("method", "").strip()
        provider_filter = filters.get("provider", "").strip()
        if status_filter:
            online = online.filter(status=status_filter)
            pos = pos.filter(status=status_filter)
        if method_filter:
            online = online.filter(method=method_filter)
            pos = pos.filter(method=method_filter)
        if provider_filter:
            online = online.filter(provider=provider_filter)
            pos = pos.none()
        if filters["source"] == "online":
            pos = pos.none()
        elif filters["source"] == "pos":
            online = online.none()

        rows = []
        status_totals = defaultdict(lambda: {"count": 0, "amount": Decimal("0.00")})
        method_totals = defaultdict(lambda: {
            "attempted_count": 0,
            "successful_count": 0,
            "collected_amount": Decimal("0.00"),
            "refunded_amount": Decimal("0.00"),
            "online_amount": Decimal("0.00"),
            "pos_amount": Decimal("0.00"),
        })
        daily = defaultdict(lambda: {"online": Decimal("0.00"), "pos": Decimal("0.00"), "count": 0})
        successful_amount = Decimal("0.00")
        refunded_amount = Decimal("0.00")
        for payment in online:
            occurred_at = _online_payment_occurred_at(payment)
            status_totals[payment.status]["count"] += 1
            status_totals[payment.status]["amount"] += payment.amount
            method = payment.method or payment.provider or "unspecified"
            method_totals[method]["attempted_count"] += 1
            if payment.status == Payment.Status.SUCCEEDED:
                method_totals[method]["successful_count"] += 1
                method_totals[method]["collected_amount"] += payment.amount
                method_totals[method]["online_amount"] += payment.amount
                successful_amount += payment.amount
                daily[occurred_at.date().isoformat()]["online"] += payment.amount
            elif payment.status == Payment.Status.REFUNDED:
                # A refunded row represents both the original collection and its
                # complete reversal; retain gross history before subtracting it.
                method_totals[method]["collected_amount"] += payment.amount
                method_totals[method]["refunded_amount"] += payment.amount
                successful_amount += payment.amount
                refunded_amount += payment.amount
            daily[occurred_at.date().isoformat()]["count"] += 1
            source_type = "booking" if payment.booking_id else "order" if payment.order_id else "payment"
            source_reference = payment.booking.reference if payment.booking_id else payment.order.reference if payment.order_id else ""
            rows.append({"reference": payment.reference, "source": "online", "source_type": source_type, "source_reference": source_reference, "branch_name": payment.branch.name, "customer_name": payment.customer.full_name if payment.customer else "Customer", "provider": payment.provider, "method": method, "status": payment.status, "amount": f"{payment.amount:.2f}", "occurred_at": occurred_at})
        for entry in pos:
            occurred_at = _pos_payment_occurred_at(entry)
            status_totals[entry.status]["count"] += 1
            status_totals[entry.status]["amount"] += entry.amount
            method_totals[entry.method]["attempted_count"] += 1
            if entry.status == "succeeded":
                method_totals[entry.method]["successful_count"] += 1
                method_totals[entry.method]["collected_amount"] += entry.amount
                method_totals[entry.method]["pos_amount"] += entry.amount
                successful_amount += entry.amount
                daily[occurred_at.date().isoformat()]["pos"] += entry.amount
            elif entry.status == "refunded":
                method_totals[entry.method]["collected_amount"] += entry.amount
                method_totals[entry.method]["refunded_amount"] += entry.amount
                successful_amount += entry.amount
                refunded_amount += entry.amount
            daily[occurred_at.date().isoformat()]["count"] += 1
            rows.append({"reference": entry.reference or str(entry.pk), "source": "pos", "source_type": "pos_sale", "source_reference": entry.sale.reference, "branch_name": entry.sale.branch.name, "customer_name": entry.sale.customer.full_name if entry.sale.customer else "Walk-in customer", "provider": "POS", "method": entry.method, "status": entry.status, "amount": f"{entry.amount:.2f}", "occurred_at": occurred_at, "cashier_name": entry.sale.cashier.full_name if entry.sale.cashier else "Unassigned"})

        branches = Branch.objects.filter(pk__in=branch_ids, is_active=True).order_by("name")
        all_online = Payment.objects.filter(branch_id__in=branch_ids)
        all_pos = POSPaymentEntry.objects.filter(sale__branch_id__in=branch_ids)
        methods = sorted(set(all_online.exclude(method="").values_list("method", flat=True)) | set(all_pos.values_list("method", flat=True)))
        providers = sorted(set(all_online.exclude(provider="").values_list("provider", flat=True)))
        statuses = sorted(set(all_online.values_list("status", flat=True)) | set(all_pos.values_list("status", flat=True)))
        count = len(rows)
        return Response({
            "filters": {"date_from": filters["date_from"], "date_to": filters["date_to"], "branch": str(selected_branch) if selected_branch else "", "source": filters["source"], "status": status_filter, "method": method_filter, "provider": provider_filter},
            "branches": [{"id": str(branch.pk), "name": branch.name} for branch in branches],
            "choices": {"statuses": statuses, "methods": methods, "providers": providers},
            "summary": {"payment_count": count, "successful_count": status_totals["succeeded"]["count"], "successful_amount": f"{successful_amount:.2f}", "pending_count": status_totals["pending"]["count"], "failed_count": status_totals["failed"]["count"] + status_totals["cancelled"]["count"], "refunded_count": status_totals["refunded"]["count"], "refunded_amount": f"{refunded_amount:.2f}", "net_collected": f"{successful_amount - refunded_amount:.2f}"},
            "by_status": [{"status": key, "count": values["count"], "amount": f"{values['amount']:.2f}"} for key, values in sorted(status_totals.items()) if values["count"]],
            "by_method": [
                {
                    "method": key,
                    "attempted_count": values["attempted_count"],
                    "successful_count": values["successful_count"],
                    "collected_amount": f"{values['collected_amount']:.2f}",
                    "refunded_amount": f"{values['refunded_amount']:.2f}",
                    "net_collected": f"{values['collected_amount'] - values['refunded_amount']:.2f}",
                    "online_amount": f"{values['online_amount']:.2f}",
                    "pos_amount": f"{values['pos_amount']:.2f}",
                }
                for key, values in sorted(method_totals.items())
            ],
            "daily": [{"date": key, "online": f"{values['online']:.2f}", "pos": f"{values['pos']:.2f}", "total": f"{values['online'] + values['pos']:.2f}", "count": values["count"]} for key, values in sorted(daily.items())],
            "payments": sorted(rows, key=lambda row: row["occurred_at"], reverse=True)[:1000],
        })


class ManagementBranchesReportView(APIView):
    """Cross-operational performance comparison for permitted branches."""

    permission_classes = [IsOwnerOrAssignedBranchStaff]
    required_branch_roles = (BranchStaffAssignment.Role.MANAGER,)

    class FilterSerializer(serializers.Serializer):
        date_from = serializers.DateField(required=False)
        date_to = serializers.DateField(required=False)
        branch = serializers.UUIDField(required=False)
        sort = serializers.ChoiceField(choices=(("revenue", "Revenue"), ("bookings", "Bookings"), ("payments", "Payments"), ("name", "Name")), required=False, default="revenue")

        def validate(self, attrs):
            today = timezone.localdate()
            attrs.setdefault("date_to", today + timedelta(days=30))
            attrs.setdefault("date_from", today - timedelta(days=29))
            if attrs["date_from"] > attrs["date_to"]:
                raise serializers.ValidationError({"date_to": "The end date cannot be before the start date."})
            if (attrs["date_to"] - attrs["date_from"]).days > 366:
                raise serializers.ValidationError({"date_to": "Select a reporting period of 366 days or less."})
            return attrs

    def get(self, request):
        query = self.FilterSerializer(data=request.query_params)
        query.is_valid(raise_exception=True)
        filters = query.validated_data
        branch_ids = get_accessible_branch_ids(request.user, self.required_branch_roles)
        selected_branch = filters.get("branch")
        if selected_branch and selected_branch not in branch_ids:
            raise serializers.ValidationError({"branch": "This branch is outside your reporting assignment."})
        scope = {selected_branch} if selected_branch else branch_ids
        branches = list(Branch.objects.filter(pk__in=scope, is_active=True).order_by("name"))
        metrics = {
            branch.pk: {"branch_id": str(branch.pk), "branch_code": branch.code, "branch_name": branch.name, "online_sales": Decimal("0.00"), "pos_sales": Decimal("0.00"), "booking_count": 0, "booking_value": Decimal("0.00"), "completed_bookings": 0, "cancelled_bookings": 0, "no_show_bookings": 0, "product_units": 0, "product_revenue": Decimal("0.00"), "product_cost": Decimal("0.00"), "service_count": 0, "service_revenue": Decimal("0.00"), "payments_collected": Decimal("0.00"), "stock_available": 0, "low_stock_count": 0, "out_of_stock_count": 0}
            for branch in branches
        }
        date_range = (filters["date_from"], filters["date_to"])
        orders = Order.objects.filter(branch_id__in=scope, payment_status="paid", paid_at__date__range=date_range).exclude(status__in=(Order.Status.CANCELLED, Order.Status.RETURNED, Order.Status.REFUNDED))
        for order in orders:
            metrics[order.branch_id]["online_sales"] += order.total_amount
        pos_sales = POSSale.objects.filter(branch_id__in=scope, status=POSSale.Status.COMPLETED, completed_at__date__range=date_range)
        for sale in pos_sales:
            metrics[sale.branch_id]["pos_sales"] += sale.total_amount
        bookings = Booking.objects.filter(branch_id__in=scope, preferred_start__date__range=date_range)
        for booking in bookings:
            row = metrics[booking.branch_id]
            row["booking_count"] += 1
            row["booking_value"] += booking.total_amount
            row["completed_bookings"] += booking.status == Booking.Status.COMPLETED
            row["cancelled_bookings"] += booking.status == Booking.Status.CANCELLED
            row["no_show_bookings"] += booking.status == Booking.Status.NO_SHOW
        product_lines = OrderItem.objects.select_related("order").filter(order__in=orders)
        for item in product_lines:
            metrics[item.order.branch_id]["product_units"] += item.quantity
            metrics[item.order.branch_id]["product_revenue"] += item.line_total
            metrics[item.order.branch_id]["product_cost"] += item.line_cost
        pos_lines = POSSaleLine.objects.select_related("sale").filter(sale__in=pos_sales)
        for item in pos_lines:
            row = metrics[item.sale.branch_id]
            if item.item_type == POSSaleLine.ItemType.PRODUCT:
                row["product_units"] += item.quantity
                row["product_revenue"] += item.line_total
                row["product_cost"] += item.line_cost
            else:
                row["service_count"] += item.quantity
                row["service_revenue"] += item.line_total
        booking_items = BookingServiceItem.objects.select_related("booking").filter(booking__in=bookings)
        for item in booking_items:
            metrics[item.booking.branch_id]["service_count"] += 1
            if (
                item.booking.payment_status == "paid"
                and item.booking.status
                not in (Booking.Status.CANCELLED, Booking.Status.REJECTED)
            ):
                metrics[item.booking.branch_id]["service_revenue"] += item.unit_price
        for payment in Payment.objects.filter(branch_id__in=scope, status=Payment.Status.SUCCEEDED, paid_at__date__range=date_range):
            metrics[payment.branch_id]["payments_collected"] += payment.amount
        for entry in POSPaymentEntry.objects.select_related("sale").filter(sale__branch_id__in=scope, status="succeeded", created_at__date__range=date_range):
            metrics[entry.sale.branch_id]["payments_collected"] += entry.amount
        for inventory in BranchInventory.objects.filter(branch_id__in=scope):
            row = metrics[inventory.branch_id]
            available = inventory.quantity_available
            row["stock_available"] += available
            row["out_of_stock_count"] += available <= 0
            row["low_stock_count"] += 0 < available <= inventory.reorder_level

        rows = []
        combined_sales = sum(
            (values["online_sales"] + values["pos_sales"] for values in metrics.values()),
            Decimal("0.00"),
        )
        for values in metrics.values():
            total_sales = values["online_sales"] + values["pos_sales"]
            product_gross_profit = values["product_revenue"] - values["product_cost"]
            estimated_operating_result = product_gross_profit + values["service_revenue"]
            rows.append({**values, "total_sales": f"{total_sales:.2f}", "sales_share_percent": f"{((total_sales / combined_sales) * 100) if combined_sales else Decimal('0.00'):.2f}", "online_sales": f"{values['online_sales']:.2f}", "pos_sales": f"{values['pos_sales']:.2f}", "booking_value": f"{values['booking_value']:.2f}", "cancellation_rate": f"{((Decimal(values['cancelled_bookings']) / values['booking_count']) * 100) if values['booking_count'] else Decimal('0.00'):.2f}", "no_show_rate": f"{((Decimal(values['no_show_bookings']) / values['booking_count']) * 100) if values['booking_count'] else Decimal('0.00'):.2f}", "product_revenue": f"{values['product_revenue']:.2f}", "product_cost": f"{values['product_cost']:.2f}", "product_gross_profit": f"{product_gross_profit:.2f}", "service_revenue": f"{values['service_revenue']:.2f}", "estimated_operating_result": f"{estimated_operating_result:.2f}", "payments_collected": f"{values['payments_collected']:.2f}"})
        sort = filters["sort"]
        if sort == "name":
            rows.sort(key=lambda row: row["branch_name"])
        elif sort == "bookings":
            rows.sort(key=lambda row: (-row["booking_count"], row["branch_name"]))
        elif sort == "payments":
            rows.sort(key=lambda row: (-Decimal(row["payments_collected"]), row["branch_name"]))
        else:
            rows.sort(key=lambda row: (-Decimal(row["total_sales"]), row["branch_name"]))
        permitted_branches = Branch.objects.filter(pk__in=branch_ids, is_active=True).order_by("name")
        return Response({
            "filters": {"date_from": filters["date_from"], "date_to": filters["date_to"], "branch": str(selected_branch) if selected_branch else "", "sort": sort},
            "branches": [{"id": str(branch.pk), "name": branch.name} for branch in permitted_branches],
            "summary": {"branch_count": len(rows), "total_sales": f"{sum((Decimal(row['total_sales']) for row in rows), Decimal('0.00')):.2f}", "booking_count": sum(row["booking_count"] for row in rows), "booking_value": f"{sum((Decimal(row['booking_value']) for row in rows), Decimal('0.00')):.2f}", "payments_collected": f"{sum((Decimal(row['payments_collected']) for row in rows), Decimal('0.00')):.2f}", "product_revenue": f"{sum((Decimal(row['product_revenue']) for row in rows), Decimal('0.00')):.2f}", "product_gross_profit": f"{sum((Decimal(row['product_gross_profit']) for row in rows), Decimal('0.00')):.2f}", "service_revenue": f"{sum((Decimal(row['service_revenue']) for row in rows), Decimal('0.00')):.2f}", "estimated_operating_result": f"{sum((Decimal(row['estimated_operating_result']) for row in rows), Decimal('0.00')):.2f}", "stock_available": sum(row["stock_available"] for row in rows)},
            "performance": rows,
        })


class ManagementReportExportView(APIView):
    """Export one permission-scoped management report using its canonical API data."""

    permission_classes = [IsOwnerOrAssignedBranchStaff]
    required_branch_roles = (BranchStaffAssignment.Role.MANAGER,)

    report_views = {
        "sales": ManagementSalesReportView,
        "bookings": ManagementBookingsReportView,
        "products": ManagementProductsReportView,
        "services": ManagementServicesReportView,
        "inventory": ManagementInventoryReportView,
        "payments": ManagementPaymentsReportView,
        "branches": ManagementBranchesReportView,
    }

    def get(self, request, report_name):
        if report_name not in REPORTS:
            raise serializers.ValidationError({"report": "Select a supported report."})
        export_format = request.query_params.get("file_format", "pdf").lower()
        if export_format not in {"pdf", "xlsx", "csv"}:
            raise serializers.ValidationError({"format": "Use pdf, xlsx, or csv."})
        report_response = self.report_views[report_name]().get(request)
        payload = report_response.data
        exporters = {"pdf": export_pdf, "xlsx": export_excel, "csv": export_csv}
        return exporters[export_format](report_name, payload, request.user)
