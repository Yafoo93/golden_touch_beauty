from django.shortcuts import render

from decimal import Decimal

from django.db import transaction
from django.db.models import Count, Q, Sum
from django.utils import timezone
from rest_framework import generics, serializers
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models import User
from auditlog.models import AuditLog
from auditlog.services import actor_role_for, client_device, client_ip, record_event
from branches.models import Branch, BranchStaffAssignment
from branches.permissions import IsOwnerOrAssignedBranchStaff, can_access_branch, get_accessible_branch_ids, is_owner
from inventory.models import BranchInventory, StockMovement
from services.models import Service

from .models import POSPaymentEntry, POSSale, POSSaleLine


class POSSaleLineSerializer(serializers.ModelSerializer):
    class Meta:
        model = POSSaleLine
        fields = ("id", "item_type", "item_reference", "name", "option_name", "sku", "quantity", "unit_price", "line_total")


class POSPaymentEntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = POSPaymentEntry
        fields = ("id", "method", "reference", "amount", "status", "created_at")


class POSSaleHistorySerializer(serializers.ModelSerializer):
    branch_id = serializers.UUIDField(source="branch.id", read_only=True)
    branch_code = serializers.CharField(source="branch.code", read_only=True)
    branch_name = serializers.CharField(source="branch.name", read_only=True)
    cashier_name = serializers.SerializerMethodField()
    cashier_id = serializers.UUIDField(read_only=True)
    customer_name = serializers.SerializerMethodField()
    status_label = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = POSSale
        fields = (
            "id", "reference", "branch_id", "branch_code", "branch_name",
            "cashier_id", "cashier_name", "customer_name", "status", "status_label",
            "payment_status", "currency", "total_amount", "item_count",
            "completed_at", "created_at",
        )

    def get_cashier_name(self, sale):
        return sale.cashier.full_name if sale.cashier else "Unassigned"

    def get_customer_name(self, sale):
        return sale.customer.full_name if sale.customer else "Walk-in customer"


class POSLineInputSerializer(serializers.Serializer):
    item_type = serializers.ChoiceField(choices=POSSaleLine.ItemType.choices)
    item_reference = serializers.UUIDField()
    quantity = serializers.IntegerField(min_value=1, max_value=99)


class POSPaymentInputSerializer(serializers.Serializer):
    method = serializers.ChoiceField(choices=(
        ("cash", "Cash"),
        ("card", "Card/electronic"),
        ("mobile_money", "Mobile money"),
        ("bank_transfer", "Bank transfer"),
    ))
    amount = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=Decimal("0.01"))
    reference = serializers.CharField(required=False, allow_blank=True, max_length=150)

    def validate(self, attrs):
        if attrs["method"] != "cash" and not attrs.get("reference", "").strip():
            raise serializers.ValidationError({"reference": "A transaction or transfer reference is required."})
        return attrs


class POSCreateSerializer(serializers.Serializer):
    branch = serializers.UUIDField()
    customer = serializers.UUIDField(required=False, allow_null=True)
    lines = POSLineInputSerializer(many=True, allow_empty=False)
    payments = POSPaymentInputSerializer(many=True, allow_empty=False)


class POSSaleHistoryView(generics.ListAPIView):
    serializer_class = POSSaleHistorySerializer
    permission_classes = [IsOwnerOrAssignedBranchStaff]
    required_branch_roles = (
        BranchStaffAssignment.Role.MANAGER,
        BranchStaffAssignment.Role.CASHIER,
    )

    @transaction.atomic
    def post(self, request):
        payload = POSCreateSerializer(data=request.data)
        payload.is_valid(raise_exception=True)
        data = payload.validated_data
        branch_ids = get_accessible_branch_ids(request.user, self.required_branch_roles)
        if data["branch"] not in branch_ids:
            raise serializers.ValidationError({"branch": "This branch is outside your POS assignment."})
        branch = Branch.objects.get(pk=data["branch"], is_active=True)

        customer = None
        if data.get("customer"):
            customer = User.objects.filter(
                pk=data["customer"], is_active=True, is_staff=False,
            ).first()
            if customer is None:
                raise serializers.ValidationError({"customer": "Select a valid active customer or use walk-in."})

        snapshots = []
        inventory_deductions = []
        seen = set()
        total = Decimal("0.00")
        for line in data["lines"]:
            key = (line["item_type"], line["item_reference"])
            if key in seen:
                raise serializers.ValidationError({"lines": "Each product or service may appear only once."})
            seen.add(key)
            quantity = line["quantity"]
            if line["item_type"] == POSSaleLine.ItemType.PRODUCT:
                inventory = BranchInventory.objects.select_for_update().select_related(
                    "product_variant", "product_variant__product",
                ).filter(
                    branch=branch, product_variant_id=line["item_reference"], is_available=True,
                    product_variant__is_active=True, product_variant__product__is_active=True,
                    product_variant__product__is_published=True,
                ).first()
                if inventory is None or inventory.quantity_available < quantity:
                    raise serializers.ValidationError({"lines": "A selected product is unavailable in the requested quantity."})
                variant = inventory.product_variant
                snapshot = {
                    "item_type": POSSaleLine.ItemType.PRODUCT,
                    "item_reference": str(variant.pk), "name": variant.product.name,
                    "option_name": variant.name, "sku": variant.sku,
                    "quantity": quantity, "unit_price": variant.selling_price,
                }
                inventory_deductions.append((inventory, quantity))
            else:
                service = Service.objects.filter(
                    pk=line["item_reference"], is_active=True, is_published=True,
                    branch_availability__branch=branch,
                    branch_availability__is_available=True,
                ).distinct().first()
                if service is None:
                    raise serializers.ValidationError({"lines": "A selected service is unavailable at this branch."})
                snapshot = {
                    "item_type": POSSaleLine.ItemType.SERVICE,
                    "item_reference": str(service.pk), "name": service.name,
                    "option_name": f"{service.duration_minutes} minutes", "sku": "",
                    "quantity": quantity, "unit_price": service.price,
                }
            snapshot["line_total"] = snapshot["unit_price"] * quantity
            total += snapshot["line_total"]
            snapshots.append(snapshot)

        paid = sum((entry["amount"] for entry in data["payments"]), Decimal("0.00"))
        if paid > total:
            raise serializers.ValidationError({"payments": "Payment entries cannot exceed the sale total."})

        sale = POSSale.objects.create(
            branch=branch, cashier=request.user, customer=customer,
            status=POSSale.Status.DRAFT,
            payment_status="paid" if paid == total else "partially_paid",
            total_amount=total,
            item_count=sum(snapshot["quantity"] for snapshot in snapshots),
        )
        POSSaleLine.objects.bulk_create([
            POSSaleLine(sale=sale, **snapshot) for snapshot in snapshots
        ])
        POSPaymentEntry.objects.bulk_create([
            POSPaymentEntry(
                sale=sale, method=entry["method"], amount=entry["amount"],
                reference=entry.get("reference", "").strip(), status="succeeded",
            )
            for entry in data["payments"]
        ])
        for inventory, quantity in inventory_deductions:
            inventory.quantity_on_hand -= quantity
            inventory.save(update_fields=["quantity_on_hand", "updated_at"])
            StockMovement.objects.create(
                inventory=inventory,
                movement_type=StockMovement.MovementType.SALE,
                quantity_on_hand_change=-quantity,
                quantity_reserved_change=0,
                quantity_on_hand_after=inventory.quantity_on_hand,
                quantity_reserved_after=inventory.quantity_reserved,
                reference_type="pos_sale",
                reference_id=sale.reference,
                note=f"POS sale {sale.reference}",
                performed_by=request.user,
            )
        sale.status = POSSale.Status.COMPLETED
        sale.completed_at = timezone.now()
        sale.save(update_fields=["status", "completed_at", "updated_at"])
        sale = POSSale.objects.select_related("branch", "cashier", "customer").prefetch_related(
            "lines", "payment_entries",
        ).get(pk=sale.pk)
        response = POSSaleDetailSerializer(sale).data
        response["paid_amount"] = f"{paid:.2f}"
        response["outstanding_amount"] = f"{total - paid:.2f}"
        return Response(response, status=201)

    def get_queryset(self):
        branch_ids = get_accessible_branch_ids(self.request.user, self.required_branch_roles)
        queryset = POSSale.objects.select_related("branch", "cashier", "customer").filter(branch_id__in=branch_ids)
        branch = self.request.query_params.get("branch", "").strip()
        status_value = self.request.query_params.get("status", "").strip()
        date_from = self.request.query_params.get("date_from", "").strip()
        date_to = self.request.query_params.get("date_to", "").strip()
        search = self.request.query_params.get("search", "").strip()
        if branch:
            queryset = queryset.filter(branch_id=branch)
        if status_value:
            queryset = queryset.filter(status=status_value)
        if date_from:
            queryset = queryset.filter(created_at__date__gte=date_from)
        if date_to:
            queryset = queryset.filter(created_at__date__lte=date_to)
        if search:
            queryset = queryset.filter(
                Q(reference__icontains=search)
                | Q(cashier__full_name__icontains=search)
                | Q(customer__full_name__icontains=search)
            )
        return queryset


class POSSaleDetailSerializer(POSSaleHistorySerializer):
    branch_address = serializers.CharField(source="branch.address", read_only=True)
    lines = POSSaleLineSerializer(many=True, read_only=True)
    payments = POSPaymentEntrySerializer(source="payment_entries", many=True, read_only=True)
    can_correct = serializers.SerializerMethodField()
    corrections = serializers.SerializerMethodField()

    class Meta(POSSaleHistorySerializer.Meta):
        fields = POSSaleHistorySerializer.Meta.fields + (
            "receipt_reference", "branch_address", "lines", "payments", "can_correct", "corrections",
        )

    def get_can_correct(self, sale):
        request = self.context.get("request")
        return bool(
            sale.status == POSSale.Status.COMPLETED
            and request
            and can_access_branch(
                request.user, sale.branch_id,
                (BranchStaffAssignment.Role.MANAGER,),
            )
        )

    def get_corrections(self, sale):
        events = AuditLog.objects.select_related("actor").filter(
            record_type="pos_sale", record_id=sale.reference,
            action__in=("pos.sale_reversed", "pos.sale_refunded"),
        )
        return [
            {
                "action": event.action,
                "reason": event.reason,
                "actor_name": event.actor.full_name if event.actor else "Former staff account",
                "created_at": event.created_at,
                "previous_values": event.previous_values,
                "new_values": event.new_values,
            }
            for event in events
        ]


class POSSaleDetailView(generics.RetrieveAPIView):
    serializer_class = POSSaleDetailSerializer
    permission_classes = [IsOwnerOrAssignedBranchStaff]
    required_branch_roles = POSSaleHistoryView.required_branch_roles
    lookup_field = "reference"

    def get_queryset(self):
        branch_ids = get_accessible_branch_ids(self.request.user, self.required_branch_roles)
        return POSSale.objects.select_related("branch", "cashier", "customer").prefetch_related("lines", "payment_entries").filter(
            branch_id__in=branch_ids,
            status__in=(POSSale.Status.COMPLETED, POSSale.Status.REFUNDED, POSSale.Status.VOIDED),
        )


class POSSaleCorrectionView(APIView):
    """Perform an auditable manager-authorized reversal or refund."""

    permission_classes = [IsOwnerOrAssignedBranchStaff]
    required_branch_roles = (BranchStaffAssignment.Role.MANAGER,)

    class InputSerializer(serializers.Serializer):
        correction_type = serializers.ChoiceField(choices=(("reversal", "Reversal"), ("refund", "Refund")))
        reason = serializers.CharField(min_length=10, max_length=1000, trim_whitespace=True)

    @transaction.atomic
    def post(self, request, reference):
        payload = self.InputSerializer(data=request.data)
        payload.is_valid(raise_exception=True)
        sale = POSSale.objects.select_for_update().select_related("branch", "cashier", "customer").filter(
            reference=reference,
        ).first()
        if sale is None:
            return Response({"detail": "Sale not found."}, status=404)
        if not can_access_branch(request.user, sale.branch_id, self.required_branch_roles):
            self.permission_denied(request, message="Only an assigned branch manager or owner can correct this sale.")
        if sale.status != POSSale.Status.COMPLETED:
            raise serializers.ValidationError({"sale": "Only a completed sale can be reversed or refunded."})

        correction_type = payload.validated_data["correction_type"]
        reason = payload.validated_data["reason"]
        target_status = POSSale.Status.REFUNDED if correction_type == "refund" else POSSale.Status.VOIDED
        target_payment_status = "refunded" if correction_type == "refund" else "voided"
        payment_entry_status = "refunded" if correction_type == "refund" else "cancelled"
        previous = {
            "status": sale.status,
            "payment_status": sale.payment_status,
            "total_amount": str(sale.total_amount),
        }

        for line in sale.lines.filter(item_type=POSSaleLine.ItemType.PRODUCT):
            inventory = BranchInventory.objects.select_for_update().get(
                branch=sale.branch, product_variant_id=line.item_reference,
            )
            inventory.quantity_on_hand += line.quantity
            inventory.save(update_fields=["quantity_on_hand", "updated_at"])
            StockMovement.objects.create(
                inventory=inventory,
                movement_type=StockMovement.MovementType.RETURN,
                quantity_on_hand_change=line.quantity,
                quantity_reserved_change=0,
                quantity_on_hand_after=inventory.quantity_on_hand,
                quantity_reserved_after=inventory.quantity_reserved,
                reference_type="pos_sale_correction",
                reference_id=sale.reference,
                note=f"{correction_type.title()} of POS sale {sale.reference}: {reason}",
                performed_by=request.user,
            )

        sale.payment_entries.update(status=payment_entry_status)
        POSSale.objects.filter(pk=sale.pk).update(
            status=target_status, payment_status=target_payment_status, updated_at=timezone.now(),
        )
        record_event(
            action=f"pos.sale_{'refunded' if correction_type == 'refund' else 'reversed'}",
            record_type="pos_sale",
            record_id=sale.reference,
            actor=request.user,
            actor_role=actor_role_for(request.user),
            branch=sale.branch,
            previous_values=previous,
            new_values={
                "status": target_status,
                "payment_status": target_payment_status,
                "stock_restored": True,
            },
            ip_address=client_ip(request),
            device_identifier=client_device(request),
            reason=reason,
        )
        corrected = POSSale.objects.select_related("branch", "cashier", "customer").prefetch_related(
            "lines", "payment_entries",
        ).get(pk=sale.pk)
        return Response(POSSaleDetailSerializer(corrected, context={"request": request}).data)


class POSEndOfDayView(APIView):
    permission_classes = [IsOwnerOrAssignedBranchStaff]
    required_branch_roles = POSSaleHistoryView.required_branch_roles

    class QuerySerializer(serializers.Serializer):
        date = serializers.DateField(required=False, default=timezone.localdate)
        branch = serializers.UUIDField(required=False)

    def get(self, request):
        query = self.QuerySerializer(data=request.query_params)
        query.is_valid(raise_exception=True)
        report_date = query.validated_data["date"]
        branch_ids = get_accessible_branch_ids(request.user, self.required_branch_roles)
        selected_branch = query.validated_data.get("branch")
        if selected_branch and selected_branch not in branch_ids:
            raise serializers.ValidationError({"branch": "This branch is outside your POS assignment."})

        assignments = BranchStaffAssignment.objects.filter(
            staff=request.user, is_active=True, branch_id__in=branch_ids
        ).values_list("roles", flat=True)
        can_review_team = is_owner(request.user) or any(
            BranchStaffAssignment.Role.MANAGER in (roles or []) for roles in assignments
        )
        sales = POSSale.objects.filter(
            branch_id__in=({selected_branch} if selected_branch else branch_ids),
            status=POSSale.Status.COMPLETED,
        ).filter(
            Q(completed_at__date=report_date)
            | Q(completed_at__isnull=True, created_at__date=report_date)
        )
        if not can_review_team:
            sales = sales.filter(cashier=request.user)

        gross_total = sales.aggregate(total=Sum("total_amount"))["total"] or Decimal("0.00")
        payments = POSPaymentEntry.objects.filter(sale__in=sales, status="succeeded")
        payment_total = payments.aggregate(total=Sum("amount"))["total"] or Decimal("0.00")
        payment_methods = [
            {"method": row["method"], "sale_count": row["sale_count"], "amount": f"{row['amount']:.2f}"}
            for row in payments.values("method").annotate(sale_count=Count("sale", distinct=True), amount=Sum("amount")).order_by("method")
        ]
        cashier_totals = [
            {
                "cashier_id": str(row["cashier_id"]) if row["cashier_id"] else None,
                "cashier_name": row["cashier__full_name"] or "Unassigned",
                "sale_count": row["sale_count"],
                "item_count": row["item_count"] or 0,
                "amount": f"{row['amount']:.2f}",
            }
            for row in sales.values("cashier_id", "cashier__full_name").annotate(
                sale_count=Count("id"), item_count=Sum("item_count"), amount=Sum("total_amount")
            ).order_by("cashier__full_name")
        ]
        branches = Branch.objects.filter(pk__in=branch_ids, is_active=True).order_by("name")
        return Response({
            "date": report_date,
            "scope": "team" if can_review_team else "cashier",
            "branches": [{"id": str(branch.pk), "code": branch.code, "name": branch.name} for branch in branches],
            "selected_branch": str(selected_branch) if selected_branch else None,
            "summary": {
                "sale_count": sales.count(), "item_count": sales.aggregate(total=Sum("item_count"))["total"] or 0,
                "gross_total": f"{gross_total:.2f}", "payment_total": f"{payment_total:.2f}",
                "difference": f"{gross_total - payment_total:.2f}",
            },
            "payment_methods": payment_methods,
            "cashiers": cashier_totals,
        })


class POSWorkspaceView(APIView):
    """Return the branch-scoped catalogue used to compose a current POS sale."""

    permission_classes = [IsOwnerOrAssignedBranchStaff]
    required_branch_roles = (
        BranchStaffAssignment.Role.MANAGER,
        BranchStaffAssignment.Role.CASHIER,
    )

    class QuerySerializer(serializers.Serializer):
        branch = serializers.UUIDField(required=False)
        search = serializers.CharField(required=False, max_length=150, allow_blank=True)

    def get(self, request):
        query = self.QuerySerializer(data=request.query_params)
        query.is_valid(raise_exception=True)
        branch_ids = get_accessible_branch_ids(request.user, self.required_branch_roles)
        branches = list(Branch.objects.filter(pk__in=branch_ids, is_active=True).order_by("name"))
        selected_id = query.validated_data.get("branch")
        if selected_id and selected_id not in branch_ids:
            raise serializers.ValidationError({"branch": "This branch is outside your POS assignment."})
        selected = next((branch for branch in branches if branch.pk == selected_id), None)
        if selected is None and len(branches) == 1:
            selected = branches[0]

        products = []
        services = []
        if selected:
            search = query.validated_data.get("search", "").strip()
            stocks = BranchInventory.objects.select_related(
                "product_variant", "product_variant__product", "product_variant__product__category"
            ).filter(
                branch=selected,
                is_available=True,
                product_variant__is_active=True,
                product_variant__product__is_active=True,
                product_variant__product__is_published=True,
            )
            if search:
                stocks = stocks.filter(
                    Q(product_variant__product__name__icontains=search)
                    | Q(product_variant__name__icontains=search)
                    | Q(product_variant__sku__icontains=search)
                )
            for stock in stocks.order_by("product_variant__product__name", "product_variant__name"):
                if stock.quantity_available <= 0:
                    continue
                product = stock.product_variant.product
                products.append({
                    "id": str(stock.product_variant_id), "type": "product",
                    "name": product.name, "option": stock.product_variant.name,
                    "sku": stock.product_variant.sku,
                    "category": product.category.name,
                    "price": f"{stock.product_variant.selling_price:.2f}",
                    "available_quantity": stock.quantity_available,
                    "image_path": f"/{product.image.url.lstrip('/')}" if product.image else product.image_path,
                })

            service_queryset = Service.objects.select_related("category").filter(
                branch_availability__branch=selected,
                branch_availability__is_available=True,
                is_active=True,
                is_published=True,
            ).distinct()
            if search:
                service_queryset = service_queryset.filter(
                    Q(name__icontains=search) | Q(category__name__icontains=search)
                )
            for service in service_queryset.order_by("category__display_order", "name"):
                services.append({
                    "id": str(service.pk), "type": "service", "name": service.name,
                    "option": f"{service.duration_minutes} minutes", "sku": "",
                    "category": service.category.name, "price": f"{service.price:.2f}",
                    "available_quantity": None,
                    "image_path": f"/{service.image.url.lstrip('/')}" if service.image else service.image_path,
                })

        return Response({
            "branches": [{"id": str(branch.pk), "code": branch.code, "name": branch.name} for branch in branches],
            "selected_branch": str(selected.pk) if selected else None,
            "products": products,
            "services": services,
        })


class POSCustomerSearchView(APIView):
    """Search active customer accounts for an assigned POS branch."""

    permission_classes = [IsOwnerOrAssignedBranchStaff]
    required_branch_roles = POSWorkspaceView.required_branch_roles

    class QuerySerializer(serializers.Serializer):
        branch = serializers.UUIDField(required=True)
        search = serializers.CharField(required=True, min_length=2, max_length=150, trim_whitespace=True)

    def get(self, request):
        query = self.QuerySerializer(data=request.query_params)
        query.is_valid(raise_exception=True)
        branch_id = query.validated_data["branch"]
        branch_ids = get_accessible_branch_ids(request.user, self.required_branch_roles)
        if branch_id not in branch_ids:
            raise serializers.ValidationError({"branch": "This branch is outside your POS assignment."})

        search = query.validated_data["search"]
        customers = User.objects.filter(is_active=True, is_staff=False).filter(
            Q(full_name__icontains=search)
            | Q(email__icontains=search)
            | Q(phone_number__icontains=search)
        ).order_by("full_name")[:10]
        return Response({
            "results": [
                {
                    "id": str(customer.pk),
                    "full_name": customer.full_name,
                    "email": customer.email,
                    "phone_number": customer.phone_number,
                }
                for customer in customers
            ]
        })
