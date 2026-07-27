import logging

from django.db import connection
from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework import generics, serializers
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from auditlog.services import actor_role_for, client_device, client_ip, record_event
from branches.permissions import IsOwner

from .exceptions import error_payload
from .models import GalleryItem, Testimonial, WebsiteContent
from .serializers import (
    GalleryItemSerializer,
    ManagementGalleryItemSerializer,
    ManagementWebsiteContentSerializer,
    PublicWebsiteContentSerializer,
    ManagementTestimonialSerializer,
    TestimonialSerializer,
)


logger = logging.getLogger("golden_touch.health")


@extend_schema(
    responses=inline_serializer(
        name="PingResponse",
        fields={"status": serializers.CharField()},
    )
)
@api_view(["GET"])
@permission_classes([AllowAny])
def ping(request):
    """Lightweight availability probe that does not query the database."""
    return Response({"status": "ok"})


@extend_schema(
    responses=inline_serializer(
        name="HealthResponse",
        fields={
            "application": serializers.CharField(),
            "status": serializers.CharField(),
            "database": serializers.CharField(),
        },
    )
)
@api_view(["GET"])
@permission_classes([AllowAny])
def health_check(request):
    database_status = "connected"

    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
    except Exception:
        database_status = "disconnected"
        logger.exception("database_health_check_failed")

    return Response(
        {
            "application": "Golden Touch Beauty Centre",
            "status": "ok",
            "database": database_status,
        }
    )


@api_view(["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"])
@permission_classes([AllowAny])
def api_not_found(request, path=None):
    return Response(
        error_payload(
            code="not_found",
            message="The requested API endpoint was not found.",
            status_code=404,
            request_id=getattr(request, "request_id", None),
        ),
        status=404,
    )


class ClientErrorSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=100, required=False, default="Error")
    message = serializers.CharField(max_length=500)
    digest = serializers.CharField(max_length=200, required=False, allow_blank=True)
    path = serializers.CharField(max_length=500, required=False, allow_blank=True)


@extend_schema(
    request=ClientErrorSerializer,
    responses={202: None},
)
@api_view(["POST"])
@permission_classes([AllowAny])
def report_client_error(request):
    serializer = ClientErrorSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    data = serializer.validated_data
    logger.error(
        "client_error_reported",
        extra={
            "error_name": data["name"],
            "error_message": data["message"],
            "error_digest": data.get("digest", ""),
            "client_path": data.get("path", ""),
        },
    )
    return Response(status=202)


class PublicWebsiteContentListView(generics.ListAPIView):
    authentication_classes = []
    permission_classes = [AllowAny]
    pagination_class = None
    serializer_class = PublicWebsiteContentSerializer
    queryset = WebsiteContent.objects.filter(is_published=True).order_by(
        "page", "section", "label"
    )


class ManagementWebsiteContentListView(generics.ListAPIView):
    permission_classes = [IsOwner]
    pagination_class = None
    serializer_class = ManagementWebsiteContentSerializer
    queryset = WebsiteContent.objects.select_related("updated_by").order_by(
        "page", "section", "label"
    )


class ManagementWebsiteContentDetailView(generics.RetrieveUpdateAPIView):
    permission_classes = [IsOwner]
    http_method_names = ["get", "patch", "head", "options"]
    serializer_class = ManagementWebsiteContentSerializer
    queryset = WebsiteContent.objects.select_related("updated_by")

    def perform_update(self, serializer):
        content = self.get_object()
        previous_values = {
            "value": content.value,
            "is_published": content.is_published,
        }
        updated = serializer.save(updated_by=self.request.user)
        record_event(
            action="website_content.updated",
            record_type="WebsiteContent",
            record_id=updated.id,
            actor=self.request.user,
            actor_role=actor_role_for(self.request.user),
            previous_values=previous_values,
            new_values={
                "value": updated.value,
                "is_published": updated.is_published,
            },
            ip_address=client_ip(self.request),
            device_identifier=client_device(self.request),
        )


class PublicGalleryItemListView(generics.ListAPIView):
    authentication_classes = []
    permission_classes = [AllowAny]
    pagination_class = None
    serializer_class = GalleryItemSerializer
    queryset = GalleryItem.objects.filter(is_published=True).order_by(
        "display_order", "created_at"
    )


class ManagementGalleryItemListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsOwner]
    pagination_class = None
    serializer_class = ManagementGalleryItemSerializer
    queryset = GalleryItem.objects.select_related("updated_by").order_by(
        "display_order", "created_at"
    )

    def perform_create(self, serializer):
        item = serializer.save(updated_by=self.request.user)
        record_event(
            action="gallery_item.created",
            record_type="GalleryItem",
            record_id=item.id,
            actor=self.request.user,
            actor_role=actor_role_for(self.request.user),
            new_values={
                "title": item.title,
                "is_published": item.is_published,
            },
            ip_address=client_ip(self.request),
            device_identifier=client_device(self.request),
        )


class ManagementGalleryItemDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsOwner]
    serializer_class = ManagementGalleryItemSerializer
    queryset = GalleryItem.objects.select_related("updated_by")

    def perform_update(self, serializer):
        item = self.get_object()
        previous_image = item.image.name if item.image else ""
        previous_values = {
            "title": item.title,
            "category": item.category,
            "alt_text": item.alt_text,
            "display_size": item.display_size,
            "display_order": item.display_order,
            "is_published": item.is_published,
        }
        updated = serializer.save(updated_by=self.request.user)
        if previous_image and updated.image.name != previous_image:
            updated.image.storage.delete(previous_image)
        record_event(
            action="gallery_item.updated",
            record_type="GalleryItem",
            record_id=updated.id,
            actor=self.request.user,
            actor_role=actor_role_for(self.request.user),
            previous_values=previous_values,
            new_values={
                "title": updated.title,
                "category": updated.category,
                "alt_text": updated.alt_text,
                "display_size": updated.display_size,
                "display_order": updated.display_order,
                "is_published": updated.is_published,
            },
            ip_address=client_ip(self.request),
            device_identifier=client_device(self.request),
        )

    def perform_destroy(self, instance):
        image_name = instance.image.name if instance.image else ""
        record_event(
            action="gallery_item.deleted",
            record_type="GalleryItem",
            record_id=instance.id,
            actor=self.request.user,
            actor_role=actor_role_for(self.request.user),
            previous_values={"title": instance.title},
            ip_address=client_ip(self.request),
            device_identifier=client_device(self.request),
        )
        storage = instance.image.storage if instance.image else None
        instance.delete()
        if image_name and storage:
            storage.delete(image_name)


class PublicTestimonialListView(generics.ListAPIView):
    authentication_classes = []
    permission_classes = [AllowAny]
    pagination_class = None
    serializer_class = TestimonialSerializer
    queryset = Testimonial.objects.filter(
        moderation_status=Testimonial.ModerationStatus.APPROVED,
        consent_confirmed=True,
        is_visible=True,
    ).order_by("display_order", "-created_at")


class ManagementTestimonialListView(generics.ListAPIView):
    permission_classes = [IsOwner]
    pagination_class = None
    serializer_class = ManagementTestimonialSerializer
    queryset = Testimonial.objects.select_related("reviewed_by").order_by(
        "display_order", "-created_at"
    )


class ManagementTestimonialDetailView(generics.RetrieveUpdateAPIView):
    permission_classes = [IsOwner]
    http_method_names = ["get", "patch", "head", "options"]
    serializer_class = ManagementTestimonialSerializer
    queryset = Testimonial.objects.select_related("reviewed_by")

    def perform_update(self, serializer):
        testimonial = self.get_object()
        previous_values = {
            "consent_confirmed": testimonial.consent_confirmed,
            "moderation_status": testimonial.moderation_status,
            "is_visible": testimonial.is_visible,
            "is_featured": testimonial.is_featured,
            "display_order": testimonial.display_order,
        }
        testimonial.mark_reviewed(self.request.user)
        updated = serializer.save(
            reviewed_by=testimonial.reviewed_by,
            reviewed_at=testimonial.reviewed_at,
        )
        record_event(
            action="testimonial.moderated",
            record_type="Testimonial",
            record_id=updated.id,
            actor=self.request.user,
            actor_role=actor_role_for(self.request.user),
            previous_values=previous_values,
            new_values={
                "consent_confirmed": updated.consent_confirmed,
                "moderation_status": updated.moderation_status,
                "is_visible": updated.is_visible,
                "is_featured": updated.is_featured,
                "display_order": updated.display_order,
            },
            ip_address=client_ip(self.request),
            device_identifier=client_device(self.request),
        )
