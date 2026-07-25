import uuid

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


GALLERY_ITEMS = [
    ("Bridal styling", "Bridal & Glam", "Detailed bridal styling and traditional attire", "/images/bridal.jpeg", "tall"),
    ("Facial care", "Skin & Clinical Aesthetics", "A client receiving a professional facial treatment", "/images/facial_treatment.jpeg", "wide"),
    ("Creative makeup", "Makeup", "A colorful professionally applied makeup look", "/images/makeup1.jpeg", "standard"),
    ("Hair care", "Hair", "A professional hair treatment at a salon basin", "/images/hair_treatment.jpeg", "standard"),
    ("Gele styling", "Traditional Styling", "A finished traditional gele headwrap style", "/images/gele.jpeg", "tall"),
    ("Glam preparation", "Makeup", "Beauty products arranged for a makeup session", "/images/makeup.jpeg", "standard"),
    ("Targeted skin care", "Skin & Clinical Aesthetics", "A professional facial skin-care treatment in progress", "/images/acne.jpeg", "wide"),
    ("Professional artistry", "Makeup", "A makeup professional holding a selection of brushes", "/images/makeup2.jpeg", "standard"),
]


def seed_gallery(apps, schema_editor):
    GalleryItem = apps.get_model("core", "GalleryItem")
    for order, (title, category, alt_text, image_path, size) in enumerate(GALLERY_ITEMS, 1):
        GalleryItem.objects.get_or_create(
            title=title,
            defaults={
                "category": category,
                "alt_text": alt_text,
                "image_path": image_path,
                "display_size": size,
                "display_order": order,
                "is_published": True,
            },
        )


def remove_seed_gallery(apps, schema_editor):
    GalleryItem = apps.get_model("core", "GalleryItem")
    GalleryItem.objects.filter(title__in=[item[0] for item in GALLERY_ITEMS]).delete()


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("core", "0002_websitecontent"),
    ]

    operations = [
        migrations.CreateModel(
            name="GalleryItem",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("title", models.CharField(max_length=150)),
                ("category", models.CharField(max_length=120)),
                ("alt_text", models.CharField(max_length=250)),
                ("image", models.ImageField(blank=True, upload_to="gallery/%Y/%m/")),
                ("image_path", models.CharField(blank=True, max_length=255)),
                ("display_size", models.CharField(choices=[("standard", "Standard"), ("wide", "Wide"), ("tall", "Tall")], default="standard", max_length=20)),
                ("display_order", models.PositiveSmallIntegerField(default=0)),
                ("is_published", models.BooleanField(default=False)),
                ("updated_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="updated_gallery_items", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ["display_order", "created_at"]},
        ),
        migrations.RunPython(seed_gallery, remove_seed_gallery),
    ]
