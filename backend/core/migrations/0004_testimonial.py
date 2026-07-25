import uuid

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


SAMPLES = [
    (
        "Skin-care client",
        "Sample attribution — not a verified customer",
        "Skin care",
        "The consultation felt thoughtful and personal. Each step of the treatment was explained clearly, and I left feeling cared for and confident about my routine.",
    ),
    (
        "Bridal client",
        "Sample attribution — not a verified customer",
        "Bridal styling",
        "The team listened carefully to the look I wanted and helped the preparation feel calm and organized. The finished styling felt elegant and true to me.",
    ),
    (
        "Hair-care client",
        "Sample attribution — not a verified customer",
        "Hair care",
        "I appreciated the professional attention and practical advice. The experience felt welcoming from the first conversation through the final styling.",
    ),
]


def seed_samples(apps, schema_editor):
    Testimonial = apps.get_model("core", "Testimonial")
    for order, (name, attribution, service, quote) in enumerate(SAMPLES, 1):
        Testimonial.objects.get_or_create(
            client_name=name,
            quote=quote,
            defaults={
                "client_attribution": attribution,
                "service_context": service,
                "source_type": "development_sample",
                "consent_confirmed": False,
                "moderation_status": "pending",
                "is_visible": False,
                "display_order": order,
            },
        )


def remove_samples(apps, schema_editor):
    Testimonial = apps.get_model("core", "Testimonial")
    Testimonial.objects.filter(source_type="development_sample").delete()


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("core", "0003_galleryitem"),
    ]

    operations = [
        migrations.CreateModel(
            name="Testimonial",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("client_name", models.CharField(max_length=150)),
                ("client_attribution", models.CharField(blank=True, max_length=180)),
                ("service_context", models.CharField(blank=True, max_length=180)),
                ("quote", models.TextField()),
                ("source_type", models.CharField(choices=[("written", "Written testimonial"), ("video", "Video transcript"), ("development_sample", "Development sample")], default="written", max_length=30)),
                ("consent_confirmed", models.BooleanField(default=False)),
                ("moderation_status", models.CharField(choices=[("pending", "Pending review"), ("approved", "Approved"), ("rejected", "Rejected")], default="pending", max_length=20)),
                ("is_visible", models.BooleanField(default=False)),
                ("is_featured", models.BooleanField(default=False)),
                ("display_order", models.PositiveSmallIntegerField(default=0)),
                ("reviewed_at", models.DateTimeField(blank=True, null=True)),
                ("reviewed_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="reviewed_testimonials", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ["display_order", "-created_at"]},
        ),
        migrations.RunPython(seed_samples, remove_samples),
    ]
