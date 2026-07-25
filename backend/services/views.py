from django.db.models import Count, Prefetch, Q
from rest_framework import filters, generics, serializers
from rest_framework.permissions import AllowAny

from auditlog.services import actor_role_for, client_device, client_ip, record_event
from branches.models import Branch
from branches.permissions import IsOwner

from .models import (
    Service,
    ServiceBranchAvailability,
    ServiceCategory,
    ServicePriceOption,
)
from .serializers import (
    FeaturedServiceSerializer,
    ManagementServiceBranchOptionSerializer,
    ManagementServiceCategoryOptionSerializer,
    ManagementServiceCategorySerializer,
    ManagementServiceCreateSerializer,
    ManagementServiceDetailSerializer,
    ManagementServiceListSerializer,
    PublicServiceCategorySerializer,
    PublicServiceDetailSerializer,
    PublicServiceSerializer,
)


def public_availability():
    return ServiceBranchAvailability.objects.select_related("branch").filter(
        is_available=True,
        branch__is_active=True,
    )


class FeaturedServiceListView(generics.ListAPIView):
    serializer_class = FeaturedServiceSerializer
    permission_classes = [AllowAny]
    pagination_class = None

    def get_queryset(self):
        availability = public_availability()
        return (
            Service.objects.select_related("category")
            .filter(
                is_featured=True,
                is_active=True,
                is_published=True,
                category__is_active=True,
            )
            .prefetch_related(
                Prefetch("branch_availability", queryset=availability)
            )
            .order_by("category__display_order", "name")[:6]
        )


class PublicServiceListView(generics.ListAPIView):
    serializer_class = PublicServiceSerializer
    permission_classes = [AllowAny]
    pagination_class = None
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ("name", "price", "duration_minutes", "category__name")
    ordering = ("category__display_order", "name")

    def get_queryset(self):
        queryset = (
            Service.objects.select_related("category")
            .filter(
                is_active=True,
                is_published=True,
                category__is_active=True,
                branch_availability__is_available=True,
                branch_availability__branch__is_active=True,
            )
            .prefetch_related(
                Prefetch("branch_availability", queryset=public_availability())
            )
            .distinct()
        )
        category = self.request.query_params.get("category", "").strip()
        search = self.request.query_params.get("search", "").strip()
        branch = self.request.query_params.get("branch", "").strip()
        if category:
            queryset = queryset.filter(category__slug=category)
        if branch:
            queryset = queryset.filter(
                branch_availability__branch__code__iexact=branch,
                branch_availability__is_available=True,
                branch_availability__branch__is_active=True,
            )
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search)
                | Q(short_description__icontains=search)
                | Q(description__icontains=search)
                | Q(category__name__icontains=search)
            )
        return queryset


class PublicServiceCategoryListView(generics.ListAPIView):
    serializer_class = PublicServiceCategorySerializer
    permission_classes = [AllowAny]
    pagination_class = None

    def get_queryset(self):
        return (
            ServiceCategory.objects.filter(
                is_active=True,
                services__is_active=True,
                services__is_published=True,
                services__branch_availability__is_available=True,
                services__branch_availability__branch__is_active=True,
            )
            .order_by("display_order", "name")
            .distinct()
        )


class PublicServiceDetailView(generics.RetrieveAPIView):
    serializer_class = PublicServiceDetailSerializer
    permission_classes = [AllowAny]
    lookup_field = "slug"

    def get_queryset(self):
        return (
            Service.objects.select_related("category")
            .filter(
                is_active=True,
                is_published=True,
                category__is_active=True,
                branch_availability__is_available=True,
                branch_availability__branch__is_active=True,
            )
            .prefetch_related(
                Prefetch("branch_availability", queryset=public_availability()),
                Prefetch(
                    "price_options",
                    queryset=ServicePriceOption.objects.filter(is_active=True),
                ),
            )
            .distinct()
        )


class ManagementServiceListView(generics.ListCreateAPIView):
    permission_classes = [IsOwner]
    pagination_class = None

    def get_serializer_class(self):
        if self.request.method == "POST":
            return ManagementServiceCreateSerializer
        return ManagementServiceListSerializer

    def get_queryset(self):
        return (
            Service.objects.select_related("category")
            .prefetch_related(
                Prefetch(
                    "branch_availability",
                    queryset=ServiceBranchAvailability.objects.select_related(
                        "branch"
                    ).order_by("branch__name"),
                )
            )
            .order_by("category__display_order", "name")
        )

    def perform_create(self, serializer):
        service = serializer.save()
        record_event(
            action="service.created",
            record_type="Service",
            record_id=service.id,
            actor=self.request.user,
            actor_role=actor_role_for(self.request.user),
            new_values={
                "name": service.name,
                "slug": service.slug,
                "category_id": str(service.category_id),
                "is_active": service.is_active,
                "is_published": service.is_published,
                "branch_ids": [
                    str(branch_id)
                    for branch_id in service.branch_availability.values_list(
                        "branch_id", flat=True
                    )
                ],
            },
            ip_address=client_ip(self.request),
            device_identifier=client_device(self.request),
        )


class ManagementServiceCategoryOptionListView(generics.ListAPIView):
    serializer_class = ManagementServiceCategoryOptionSerializer
    permission_classes = [IsOwner]
    pagination_class = None
    queryset = ServiceCategory.objects.filter(is_active=True).order_by(
        "display_order", "name"
    )


class ManagementServiceBranchOptionListView(generics.ListAPIView):
    serializer_class = ManagementServiceBranchOptionSerializer
    permission_classes = [IsOwner]
    pagination_class = None
    queryset = Branch.objects.filter(is_active=True).order_by("name")


class ManagementServiceDetailView(generics.RetrieveUpdateAPIView):
    permission_classes = [IsOwner]
    http_method_names = ["get", "patch", "head", "options"]

    def get_serializer_class(self):
        if self.request.method == "PATCH":
            return ManagementServiceCreateSerializer
        return ManagementServiceDetailSerializer

    def get_queryset(self):
        return Service.objects.select_related("category").prefetch_related(
            Prefetch(
                "branch_availability",
                queryset=ServiceBranchAvailability.objects.select_related("branch"),
            ),
            Prefetch(
                "price_options",
                queryset=ServicePriceOption.objects.filter(is_active=True),
            ),
        )

    def perform_update(self, serializer):
        service = self.get_object()
        previous_image = service.image.name if service.image else ""
        previous_values = {
            "name": service.name,
            "category_id": str(service.category_id),
            "price_type": service.price_type,
            "price": str(service.price),
            "maximum_price": str(service.maximum_price) if service.maximum_price else None,
            "duration_minutes": service.duration_minutes,
            "is_active": service.is_active,
            "is_published": service.is_published,
            "branch_ids": [
                str(branch_id)
                for branch_id in service.branch_availability.filter(
                    is_available=True
                ).values_list("branch_id", flat=True)
            ],
        }
        updated = serializer.save()
        if previous_image and updated.image.name != previous_image:
            updated.image.storage.delete(previous_image)
        record_event(
            action="service.updated",
            record_type="Service",
            record_id=updated.id,
            actor=self.request.user,
            actor_role=actor_role_for(self.request.user),
            previous_values=previous_values,
            new_values={
                "name": updated.name,
                "category_id": str(updated.category_id),
                "price_type": updated.price_type,
                "price": str(updated.price),
                "maximum_price": str(updated.maximum_price) if updated.maximum_price else None,
                "duration_minutes": updated.duration_minutes,
                "is_active": updated.is_active,
                "is_published": updated.is_published,
                "branch_ids": [
                    str(branch_id)
                    for branch_id in updated.branch_availability.filter(
                        is_available=True
                    ).values_list("branch_id", flat=True)
                ],
            },
            ip_address=client_ip(self.request),
            device_identifier=client_device(self.request),
        )


class ManagementServiceCategoryListCreateView(generics.ListCreateAPIView):
    serializer_class = ManagementServiceCategorySerializer
    permission_classes = [IsOwner]
    pagination_class = None

    def get_queryset(self):
        return ServiceCategory.objects.annotate(
            service_count=Count("services")
        ).order_by("display_order", "name")

    def perform_create(self, serializer):
        category = serializer.save()
        record_event(
            action="service_category.created",
            record_type="ServiceCategory",
            record_id=category.id,
            actor=self.request.user,
            actor_role=actor_role_for(self.request.user),
            new_values={
                "name": category.name,
                "slug": category.slug,
                "display_order": category.display_order,
                "is_active": category.is_active,
            },
            ip_address=client_ip(self.request),
            device_identifier=client_device(self.request),
        )


class ManagementServiceCategoryDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = ManagementServiceCategorySerializer
    permission_classes = [IsOwner]
    http_method_names = ["get", "patch", "delete", "head", "options"]

    def get_queryset(self):
        return ServiceCategory.objects.annotate(service_count=Count("services"))

    def perform_update(self, serializer):
        category = self.get_object()
        previous_values = {
            "name": category.name,
            "description": category.description,
            "display_order": category.display_order,
            "is_active": category.is_active,
        }
        updated = serializer.save()
        record_event(
            action="service_category.updated",
            record_type="ServiceCategory",
            record_id=updated.id,
            actor=self.request.user,
            actor_role=actor_role_for(self.request.user),
            previous_values=previous_values,
            new_values={
                "name": updated.name,
                "description": updated.description,
                "display_order": updated.display_order,
                "is_active": updated.is_active,
            },
            ip_address=client_ip(self.request),
            device_identifier=client_device(self.request),
        )

    def perform_destroy(self, instance):
        if instance.services.exists():
            raise serializers.ValidationError(
                {"category": "Move or remove this category's services before deleting it."}
            )
        record_event(
            action="service_category.deleted",
            record_type="ServiceCategory",
            record_id=instance.id,
            actor=self.request.user,
            actor_role=actor_role_for(self.request.user),
            previous_values={"name": instance.name, "slug": instance.slug},
            ip_address=client_ip(self.request),
            device_identifier=client_device(self.request),
        )
        instance.delete()
