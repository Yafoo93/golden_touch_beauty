import uuid

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


APPROVED_CONTENT = [
    ("home-hero-eyebrow", "home", "Hero", "Eyebrow", "Premium beauty and wellness"),
    ("home-hero-title", "home", "Hero", "Title", "Where Beauty"),
    ("home-hero-accent-title", "home", "Hero", "Accent title", "Meets Excellence"),
    (
        "home-hero-description", "home", "Hero", "Description",
        "Discover professional beauty treatments and personal-care products at our Makola and Tse Addo branches.",
    ),
    (
        "home-cta-title", "home", "Call to action", "Title",
        "Ready to book your next visit?",
    ),
    (
        "home-cta-description", "home", "Call to action", "Description",
        "Choose a service, pick your nearest branch, and secure your appointment in minutes.",
    ),
    (
        "about-hero-description", "about", "Hero", "Description",
        "Golden Touch Beauty Centre brings professional skin, hair, body, bridal, and personal-care services together across our Makola and Tse Addo branches.",
    ),
    (
        "about-story-title", "about", "Company story", "Title",
        "Personal care, delivered with intention",
    ),
    (
        "about-story-paragraph-1", "about", "Company story", "First paragraph",
        "Golden Touch was created to give clients a trusted place for beauty, wellness, and personal care. Our work brings together clinical aesthetics, hair and bridal styling, full-body treatments, and carefully selected face and body products.",
    ),
    (
        "about-story-paragraph-2", "about", "Company story", "Second paragraph",
        "We believe a good beauty experience is more than the final result. It should begin with listening, continue with respectful and professional care, and leave every client feeling confident about the service they received.",
    ),
]


def seed_approved_content(apps, schema_editor):
    WebsiteContent = apps.get_model("core", "WebsiteContent")
    for key, page, section, label, value in APPROVED_CONTENT:
        WebsiteContent.objects.get_or_create(
            key=key,
            defaults={
                "page": page,
                "section": section,
                "label": label,
                "value": value,
                "is_published": True,
            },
        )


def remove_approved_content(apps, schema_editor):
    WebsiteContent = apps.get_model("core", "WebsiteContent")
    WebsiteContent.objects.filter(
        key__in=[item[0] for item in APPROVED_CONTENT]
    ).delete()


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("core", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="WebsiteContent",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("key", models.SlugField(max_length=120, unique=True)),
                ("page", models.CharField(db_index=True, max_length=50)),
                ("section", models.CharField(max_length=80)),
                ("label", models.CharField(max_length=150)),
                ("value", models.TextField()),
                ("is_published", models.BooleanField(default=True)),
                (
                    "updated_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="updated_website_content",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "verbose_name": "website content",
                "verbose_name_plural": "website content",
                "ordering": ["page", "section", "label"],
            },
        ),
        migrations.RunPython(seed_approved_content, remove_approved_content),
    ]
