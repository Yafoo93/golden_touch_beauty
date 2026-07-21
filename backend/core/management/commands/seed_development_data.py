from datetime import time
from decimal import Decimal

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils.text import slugify

from branches.models import Branch
from inventory.models import BranchInventory
from products.models import Product, ProductCategory, ProductVariant
from services.models import (
    Service,
    ServiceBranchAvailability,
    ServiceCategory,
)


BRANCHES = (
    {
        "code": "MAKOLA",
        "name": "Makola",
        "address": "Makola Shopping Mall, Shop 143, Second Floor, Accra, Ghana",
        "telephone_number": "+233241370429",
        "secondary_telephone_number": "+233257711182",
        "whatsapp_number": "+233241370429",
        "secondary_whatsapp_number": "+233257711182",
        "email": "",
        "google_maps_url": (
            "https://maps.google.com/maps?vet=10CAAQoqAOahcKEwj4mrSs7c-"
            "VAxUAAAAAHQAAAAAQIg..i&pvq=CgwvZy8xaGRfbDdmN2Q&fvr=1&cs=0"
            "&um=1&ie=UTF-8&fb=1&gl=gh&sa=X&ftid="
            "0xfdf90bdedf8501b:0x52470e6bd2670358"
        ),
        "opening_days": [
            "monday",
            "tuesday",
            "wednesday",
            "thursday",
            "friday",
            "saturday",
        ],
        "opening_time": time(7, 30),
        "closing_time": time(17, 0),
        "is_active": True,
    },
    {
        "code": "TSE_ADDO",
        "name": "Tse Addo",
        "address": "Tse Addo, opposite The Royal Stool Event, Accra, Ghana",
        "telephone_number": "+233241370429",
        "secondary_telephone_number": "+233207911043",
        "whatsapp_number": "+233241370429",
        "secondary_whatsapp_number": "+233207911043",
        "email": "",
        "google_maps_url": "",
        "opening_days": [
            "monday",
            "tuesday",
            "wednesday",
            "thursday",
            "friday",
            "saturday",
        ],
        "opening_time": time(7, 30),
        "closing_time": time(19, 0),
        "is_active": True,
    },
)

SERVICE_CATEGORIES = (
    ("Skin and Clinical Aesthetics", 1),
    ("Hair and Bridal/Glam", 2),
    ("Full-Body Treatment", 3),
    ("Face and Body Products", 4),
)

SERVICES = (
    {
        "name": "Facial Treatment",
        "category": "Skin and Clinical Aesthetics",
        "description": (
            "A personalized facial designed to cleanse, exfoliate, hydrate, and "
            "refresh the skin. The final treatment steps and products are selected "
            "after assessing the customer's skin needs."
        ),
        "price": "250.00",
        "duration": 60,
        "image": "/images/facial_treatment.jpeg",
    },
    {
        "name": "Sunburn Treatment",
        "category": "Skin and Clinical Aesthetics",
        "description": (
            "A soothing skin-care treatment intended to calm the appearance of "
            "sun-stressed skin, support hydration, and improve comfort. Severe "
            "burns or medical symptoms require qualified medical attention."
        ),
        "price": "220.00",
        "duration": 60,
        "image": "/images/sunburn.jpeg",
    },
    {
        "name": "Acne Treatment",
        "category": "Skin and Clinical Aesthetics",
        "description": (
            "A targeted skin-care session for acne-prone skin, focusing on gentle "
            "cleansing, congestion management, hydration, and an appropriate "
            "home-care recommendation."
        ),
        "price": "280.00",
        "duration": 60,
        "image": "/images/acne.jpeg",
    },
    {
        "name": "Hyperpigmentation and Dark-Spot Treatment",
        "category": "Skin and Clinical Aesthetics",
        "description": (
            "A tailored treatment that supports a brighter, more even-looking "
            "complexion while addressing the appearance of dark marks. Treatment "
            "selection depends on skin assessment and sensitivity."
        ),
        "price": "320.00",
        "duration": 90,
        "image": "/images/dark_spot.jpeg",
    },
    {
        "name": "Skin-Tag Removal",
        "category": "Skin and Clinical Aesthetics",
        "description": (
            "A consultation-led procedure for suitable skin tags, performed only "
            "after the treatment provider assesses eligibility, location, and "
            "relevant medical considerations."
        ),
        "price": "300.00",
        "duration": 60,
        "image": "/images/skintag.jpeg",
    },
    {
        "name": "Chemical-Burn Treatment",
        "category": "Skin and Clinical Aesthetics",
        "description": (
            "A specialist consultation and restorative care plan for skin affected "
            "by chemical irritation or burns. Active, severe, or medically urgent "
            "burns require appropriate medical care."
        ),
        "price": "400.00",
        "duration": 120,
        "image": "/images/burns_treatment.jpeg",
    },
    {
        "name": "Tattoo Removal",
        "category": "Skin and Clinical Aesthetics",
        "description": (
            "A consultation-led tattoo-removal service. The approach, number of "
            "sessions, suitability, and expected outcome depend on tattoo and skin "
            "characteristics."
        ),
        "price": "600.00",
        "duration": 120,
        "image": "/images/tattoo.jpeg",
    },
    {
        "name": "Hair Treatment",
        "category": "Hair and Bridal/Glam",
        "description": (
            "A hair and scalp care session selected for the customer's hair "
            "condition and goals, followed by suitable conditioning and finishing "
            "recommendations."
        ),
        "price": "300.00",
        "duration": 120,
        "image": "/images/hair_treatment.jpeg",
    },
    {
        "name": "Hair Styling",
        "category": "Hair and Bridal/Glam",
        "description": (
            "Professional hair preparation and styling based on the requested look, "
            "hair condition, length, and selected finishing requirements."
        ),
        "price": "250.00",
        "duration": 120,
        "image": "/images/hair_treatment.jpeg",
    },
    {
        "name": "Bridal Makeup and Styling",
        "category": "Hair and Bridal/Glam",
        "description": (
            "A bridal beauty service combining consultation, complexion preparation, "
            "makeup, and agreed styling. Group size, location, travel, and package "
            "content may change the final quotation."
        ),
        "price": "800.00",
        "duration": 120,
        "image": "/images/bridal.jpeg",
    },
    {
        "name": "Makeup Artistry",
        "category": "Hair and Bridal/Glam",
        "description": (
            "Professional makeup tailored to the customer's features, skin needs, "
            "event, and preferred finish. Product selection and intensity are agreed "
            "during the appointment."
        ),
        "price": "350.00",
        "duration": 90,
        "image": "/images/makeup.jpeg",
    },
    {
        "name": "Gele Styling",
        "category": "Hair and Bridal/Glam",
        "description": (
            "Professional gele or head-wrap styling shaped to complement the "
            "customer's outfit, event, and preferred look."
        ),
        "price": "200.00",
        "duration": 60,
        "image": "/images/gele.jpeg",
    },
    {
        "name": "Full-Body Treatment",
        "category": "Full-Body Treatment",
        "description": (
            "A consultation-led full-body beauty and wellness treatment tailored to "
            "the customer's needs. Specific treatment options and exclusions are "
            "confirmed by management."
        ),
        "price": "500.00",
        "duration": 120,
        "image": "/images/hero2.jpeg",
    },
)

PRODUCT_CATEGORIES = (
    ("Marcelito Face and Body Products", 1),
    ("Face Creams", 2),
    ("Face Serums and Oils", 3),
    ("Body Creams", 4),
    ("Body Serums and Oils", 5),
    ("Body and Face Soap", 6),
)

PRODUCTS = (
    ("Marcelito Face Cream", "Marcelito Face and Body Products", "MRC-FC-STD", "180.00", "100.00", "/images/face_cream.jpeg", "A daily face moisturizer from the Golden Touch house range, intended to support soft, comfortable, hydrated-looking skin."),
    ("Marcelito Face Serum and Oil", "Marcelito Face and Body Products", "MRC-FSO-STD", "160.00", "90.00", "/images/syrum_n_oil.jpeg", "A concentrated face-care product intended to complement a daily moisturizing routine and support a smooth, nourished appearance."),
    ("Marcelito Body Cream", "Marcelito Face and Body Products", "MRC-BC-STD", "200.00", "115.00", "/images/body_cream.jpeg", "A moisturizing body cream from the Golden Touch house range for everyday hydration and softer-feeling skin."),
    ("Marcelito Body Serum and Oil", "Marcelito Face and Body Products", "MRC-BSO-STD", "190.00", "105.00", "/images/body_syrum_oil.jpeg", "A body-care serum and oil intended to help seal in moisture and leave the skin feeling smooth."),
    ("Marcelito Body and Face Soap", "Marcelito Face and Body Products", "MRC-BFS-STD", "100.00", "55.00", "/images/body_n_face_soap.jpeg", "A cleansing product from the Golden Touch house range for body and, where the final formula permits, face use."),
    ("Face Cream", "Face Creams", "GEN-FC-STD", "150.00", "85.00", "/images/face_cream.jpeg", "A general facial moisturizer intended to support everyday hydration. Final product details must follow the actual label."),
    ("Face Serum and Oil", "Face Serums and Oils", "GEN-FSO-STD", "140.00", "75.00", "/images/syrum_n_oil.jpeg", "A facial serum or oil for use as part of a suitable skin-care routine. Final claims must follow the actual product."),
    ("Body Cream", "Body Creams", "GEN-BC-STD", "170.00", "95.00", "/images/body_cream1.jpeg", "An everyday body moisturizer intended to help keep skin feeling soft and hydrated."),
    ("Body Serum and Oil", "Body Serums and Oils", "GEN-BSO-STD", "160.00", "90.00", "/images/body_syrum_oil.jpeg", "A moisturizing body serum or oil intended to complement daily body care."),
    ("Body and Face Soap", "Body and Face Soap", "GEN-BFS-STD", "80.00", "40.00", "/images/body_n_face_soap.jpeg", "A cleansing product for body use and, only where the actual formula permits, facial use."),
)


class Command(BaseCommand):
    help = "Seed development branches, services, products, and opening stock."

    def add_arguments(self, parser):
        parser.add_argument(
            "--force",
            action="store_true",
            help="Allow the development seeder to run when DEBUG is False.",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        if not settings.DEBUG and not options["force"]:
            raise CommandError(
                "Development seeding is disabled when DEBUG is False. "
                "Use --force only in a disposable test environment."
            )

        branches = self._seed_branches()
        self._seed_services(branches)
        self._seed_products(branches)

        self.stdout.write(
            self.style.SUCCESS(
                "Development seed complete: 2 branches, 13 services, "
                "10 products, and branch opening stock."
            )
        )

    def _seed_branches(self):
        seeded = []
        for data in BRANCHES:
            code = data["code"]
            defaults = {key: value for key, value in data.items() if key != "code"}
            branch, _ = Branch.objects.update_or_create(
                code=code,
                defaults=defaults,
            )
            seeded.append(branch)
        return seeded

    def _seed_services(self, branches):
        categories = {}
        for name, display_order in SERVICE_CATEGORIES:
            category, _ = ServiceCategory.objects.update_or_create(
                slug=slugify(name),
                defaults={
                    "name": name,
                    "display_order": display_order,
                    "is_active": True,
                },
            )
            categories[name] = category

        for data in SERVICES:
            service, _ = Service.objects.update_or_create(
                slug=slugify(data["name"]),
                defaults={
                    "category": categories[data["category"]],
                    "name": data["name"],
                    "short_description": data["description"][:300],
                    "description": data["description"],
                    "price_type": Service.PriceType.FIXED,
                    "price": Decimal(data["price"]),
                    "duration_minutes": data["duration"],
                    "image_path": data["image"],
                    "is_clinic_service": True,
                    "is_home_service": False,
                    "requires_full_payment": True,
                    "allows_pay_at_clinic": True,
                    "is_active": True,
                    "is_published": True,
                },
            )
            for branch in branches:
                ServiceBranchAvailability.objects.update_or_create(
                    service=service,
                    branch=branch,
                    defaults={"is_available": True},
                )

    def _seed_products(self, branches):
        categories = {}
        for name, display_order in PRODUCT_CATEGORIES:
            category, _ = ProductCategory.objects.update_or_create(
                slug=slugify(name),
                defaults={
                    "name": name,
                    "display_order": display_order,
                    "is_active": True,
                },
            )
            categories[name] = category

        for (
            name,
            category_name,
            sku,
            selling_price,
            cost_price,
            image_path,
            description,
        ) in PRODUCTS:
            product, _ = Product.objects.update_or_create(
                slug=slugify(name),
                defaults={
                    "category": categories[category_name],
                    "name": name,
                    "brand": "Marcelito" if name.startswith("Marcelito") else "",
                    "description": description,
                    "image_path": image_path,
                    "is_active": True,
                    "is_published": True,
                },
            )
            variant, _ = ProductVariant.objects.update_or_create(
                sku=sku,
                defaults={
                    "product": product,
                    "name": "Standard",
                    "selling_price": Decimal(selling_price),
                    "cost_price": Decimal(cost_price),
                    "is_active": True,
                },
            )
            for branch in branches:
                BranchInventory.objects.get_or_create(
                    branch=branch,
                    product_variant=variant,
                    defaults={
                        "quantity_on_hand": 20,
                        "quantity_reserved": 0,
                        "reorder_level": 5,
                        "is_available": True,
                    },
                )
