import json

from django.db import transaction
from django.utils.text import slugify
from rest_framework import serializers

from branches.models import Branch
from core.uploads import RestrictedImageField, validate_image_upload
from inventory.models import BranchInventory, StockMovement
from .models import CustomerCartItem, Product, ProductCategory
from .models import ProductVariant


class FeaturedProductSerializer(serializers.ModelSerializer):
    category = serializers.CharField(source="category.name", read_only=True)
    price = serializers.SerializerMethodField()
    variant_label = serializers.SerializerMethodField()
    in_stock = serializers.SerializerMethodField()
    variant_id = serializers.SerializerMethodField()
    sku = serializers.SerializerMethodField()
    image_path = serializers.SerializerMethodField()
    contact_branches = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = (
            "name",
            "slug",
            "category",
            "description",
            "price_type",
            "price",
            "image_path",
            "variant_label",
            "variant_id",
            "sku",
            "in_stock",
            "contact_branches",
        )

    def _first_variant(self, product):
        return next(
            (variant for variant in product.variants.all() if variant.is_active),
            None,
        )

    def get_price(self, product):
        variant = self._first_variant(product)
        return format(variant.selling_price, ".2f") if variant else None

    def get_variant_label(self, product):
        variant = self._first_variant(product)
        return variant.name if variant else None

    def get_variant_id(self, product):
        variant = self._first_variant(product)
        return str(variant.id) if variant else None

    def get_sku(self, product):
        variant = self._first_variant(product)
        return variant.sku if variant else None

    def get_in_stock(self, product):
        variant = self._first_variant(product)
        if variant is None:
            return False
        return any(
            stock.is_available and stock.quantity_available > 0
            for stock in variant.branch_inventory.all()
            if stock.branch.is_active
        )

    def get_image_path(self, product):
        if product.image:
            return product.image.url
        return product.image_path

    def get_contact_branches(self, product):
        seen = set()
        result = []
        for variant in product.variants.all():
            for stock in variant.branch_inventory.all():
                branch = stock.branch
                if not stock.is_available or not branch.is_active or branch.id in seen:
                    continue
                seen.add(branch.id)
                result.append({
                    "code": branch.code,
                    "name": branch.name,
                    "whatsapp_number": branch.whatsapp_number or branch.secondary_whatsapp_number or branch.telephone_number,
                })
        return result


class PublicProductSerializer(FeaturedProductSerializer):
    category_slug = serializers.CharField(source="category.slug", read_only=True)
    availability = serializers.SerializerMethodField()

    class Meta(FeaturedProductSerializer.Meta):
        fields = FeaturedProductSerializer.Meta.fields + (
            "category_slug",
            "availability",
        )

    def _active_variants(self, product):
        return [variant for variant in product.variants.all() if variant.is_active]

    def _first_variant(self, product):
        variants = self._active_variants(product)
        return min(variants, key=lambda variant: variant.selling_price) if variants else None

    def get_variant_label(self, product):
        variants = self._active_variants(product)
        if len(variants) == 1:
            return variants[0].name
        return f"{len(variants)} options" if variants else None

    def get_in_stock(self, product):
        return any(
            stock.is_available
            and stock.branch.is_active
            and stock.quantity_available > 0
            for variant in self._active_variants(product)
            for stock in variant.branch_inventory.all()
        )

    def get_availability(self, product):
        if self.get_in_stock(product):
            return "in_stock"
        if any(variant.is_preorder for variant in self._active_variants(product)):
            return "preorder"
        return "out_of_stock"


class PublicProductCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductCategory
        fields = ("name", "slug")
        read_only_fields = fields


class PublicProductVariantSerializer(serializers.Serializer):
    id = serializers.UUIDField(read_only=True)
    name = serializers.CharField(read_only=True)
    sku = serializers.CharField(read_only=True)
    selling_price = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        read_only=True,
    )
    is_preorder = serializers.BooleanField(read_only=True)
    estimated_availability_date = serializers.DateField(read_only=True)
    availability = serializers.SerializerMethodField()
    available_at = serializers.SerializerMethodField()

    def _live_stocks(self, variant):
        return [
            stock
            for stock in variant.branch_inventory.all()
            if stock.is_available
            and stock.branch.is_active
            and stock.quantity_available > 0
        ]

    def get_availability(self, variant):
        if self._live_stocks(variant):
            return "in_stock"
        return "preorder" if variant.is_preorder else "out_of_stock"

    def get_available_at(self, variant):
        live = self._live_stocks(variant)
        if variant.is_preorder and not live:
            live = [
                stock for stock in variant.branch_inventory.all()
                if stock.is_available and stock.branch.is_active
            ]
        return [
            {
                "branch_id": str(stock.branch_id),
                "branch_code": stock.branch.code,
                "branch_name": stock.branch.name,
                "whatsapp_number": stock.branch.whatsapp_number or stock.branch.secondary_whatsapp_number or stock.branch.telephone_number,
            }
            for stock in self._live_stocks(variant)
        ]


class PublicProductDetailSerializer(serializers.ModelSerializer):
    category = serializers.CharField(source="category.name", read_only=True)
    category_slug = serializers.CharField(source="category.slug", read_only=True)
    images = serializers.SerializerMethodField()
    image_path = serializers.SerializerMethodField()
    variants = PublicProductVariantSerializer(many=True, read_only=True)

    class Meta:
        model = Product
        fields = (
            "name",
            "slug",
            "brand",
            "category",
            "category_slug",
            "description",
            "price_type",
            "image_path",
            "images",
            "variants",
        )
        read_only_fields = fields

    def get_images(self, product):
        image = self.get_image_path(product)
        return [image] if image else []

    def get_image_path(self, product):
        if product.image:
            return product.image.url
        return product.image_path


class ManagementProductListSerializer(serializers.ModelSerializer):
    category = serializers.CharField(source="category.name", read_only=True)
    publication_state = serializers.SerializerMethodField()
    active_variant_count = serializers.SerializerMethodField()
    variant_count = serializers.SerializerMethodField()
    minimum_price = serializers.SerializerMethodField()
    maximum_price = serializers.SerializerMethodField()
    total_on_hand = serializers.SerializerMethodField()
    total_reserved = serializers.SerializerMethodField()
    total_available = serializers.SerializerMethodField()
    low_stock_count = serializers.SerializerMethodField()
    branch_stock = serializers.SerializerMethodField()
    image_path = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = (
            "id",
            "name",
            "slug",
            "brand",
            "category",
            "price_type",
            "image_path",
            "is_featured",
            "is_active",
            "is_published",
            "publication_state",
            "active_variant_count",
            "variant_count",
            "minimum_price",
            "maximum_price",
            "total_on_hand",
            "total_reserved",
            "total_available",
            "low_stock_count",
            "branch_stock",
            "updated_at",
        )
        read_only_fields = fields

    def _variants(self, product):
        return list(product.variants.all())

    def get_image_path(self, product):
        if product.image:
            return product.image.url
        return product.image_path

    def _stocks(self, product):
        return [
            stock
            for variant in self._variants(product)
            for stock in variant.branch_inventory.all()
        ]

    def get_publication_state(self, product):
        if not product.is_active:
            return "inactive"
        return "published" if product.is_published else "draft"

    def get_active_variant_count(self, product):
        return sum(variant.is_active for variant in self._variants(product))

    def get_variant_count(self, product):
        return len(self._variants(product))

    def get_minimum_price(self, product):
        prices = [
            variant.selling_price
            for variant in self._variants(product)
            if variant.is_active
        ]
        return format(min(prices), ".2f") if prices else None

    def get_maximum_price(self, product):
        prices = [
            variant.selling_price
            for variant in self._variants(product)
            if variant.is_active
        ]
        return format(max(prices), ".2f") if prices else None

    def get_total_on_hand(self, product):
        return sum(stock.quantity_on_hand for stock in self._stocks(product))

    def get_total_reserved(self, product):
        return sum(stock.quantity_reserved for stock in self._stocks(product))

    def get_total_available(self, product):
        return sum(
            stock.quantity_available
            for stock in self._stocks(product)
            if stock.is_available and stock.branch.is_active
        )

    def get_low_stock_count(self, product):
        return sum(
            stock.is_available
            and stock.branch.is_active
            and stock.quantity_available <= stock.reorder_level
            for stock in self._stocks(product)
        )

    def get_branch_stock(self, product):
        summaries = {}
        for stock in self._stocks(product):
            branch = stock.branch
            summary = summaries.setdefault(
                str(branch.id),
                {
                    "branch_id": str(branch.id),
                    "branch_code": branch.code,
                    "branch_name": branch.name,
                    "branch_is_active": branch.is_active,
                    "quantity_on_hand": 0,
                    "quantity_reserved": 0,
                    "quantity_available": 0,
                },
            )
            summary["quantity_on_hand"] += stock.quantity_on_hand
            summary["quantity_reserved"] += stock.quantity_reserved
            if stock.is_available and branch.is_active:
                summary["quantity_available"] += stock.quantity_available
        return sorted(summaries.values(), key=lambda item: item["branch_name"])


class ManagementProductCategoryOptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductCategory
        fields = ("id", "name")


class ManagementProductCategorySerializer(serializers.ModelSerializer):
    product_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = ProductCategory
        fields = (
            "id",
            "name",
            "slug",
            "description",
            "display_order",
            "is_active",
            "product_count",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "id",
            "slug",
            "product_count",
            "created_at",
            "updated_at",
        )

    def _unique_slug(self, name):
        base = slugify(name) or "category"
        slug = base
        counter = 2
        while ProductCategory.objects.filter(slug=slug).exists():
            slug = f"{base}-{counter}"
            counter += 1
        return slug

    def create(self, validated_data):
        return ProductCategory.objects.create(
            slug=self._unique_slug(validated_data["name"]),
            **validated_data,
        )
        read_only_fields = fields


class ManagementProductBranchOptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Branch
        fields = ("id", "code", "name")
        read_only_fields = fields


class InitialBranchStockSerializer(serializers.Serializer):
    branch_id = serializers.UUIDField()
    quantity_on_hand = serializers.IntegerField(min_value=0, max_value=1_000_000)
    reorder_level = serializers.IntegerField(min_value=0, max_value=1_000_000)
    is_available = serializers.BooleanField(default=True)


class ManagementProductCreateSerializer(serializers.ModelSerializer):
    category_id = serializers.PrimaryKeyRelatedField(
        source="category",
        queryset=ProductCategory.objects.filter(is_active=True),
    )
    image = RestrictedImageField(write_only=True)
    publication_state = serializers.ChoiceField(
        choices=("draft", "published", "inactive"),
        default="draft",
        write_only=True,
    )
    initial_variant_name = serializers.CharField(max_length=120, write_only=True)
    initial_sku = serializers.CharField(max_length=80, write_only=True)
    initial_selling_price = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        min_value=0,
        required=False,
        allow_null=True,
        write_only=True,
    )
    initial_cost_price = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        min_value=0,
        required=False,
        allow_null=True,
        write_only=True,
    )
    initial_is_preorder = serializers.BooleanField(default=False, write_only=True)
    initial_estimated_availability_date = serializers.DateField(
        required=False, allow_null=True, write_only=True
    )
    branch_stocks = serializers.CharField(write_only=True)

    class Meta:
        model = Product
        fields = (
            "id",
            "name",
            "brand",
            "category_id",
            "description",
            "price_type",
            "image",
            "is_featured",
            "publication_state",
            "initial_variant_name",
            "initial_sku",
            "initial_selling_price",
            "initial_cost_price",
            "initial_is_preorder",
            "initial_estimated_availability_date",
            "branch_stocks",
        )
        read_only_fields = ("id",)

    def validate_image(self, image):
        return validate_image_upload(image)

    def validate_initial_sku(self, value):
        return value.strip().upper()

    def validate(self, attrs):
        raw_stocks = attrs.pop("branch_stocks")
        try:
            stock_data = json.loads(raw_stocks)
        except (TypeError, ValueError) as exc:
            raise serializers.ValidationError(
                {"branch_stocks": "Branch stock must be valid JSON."}
            ) from exc
        if not isinstance(stock_data, list) or not stock_data:
            raise serializers.ValidationError(
                {"branch_stocks": "Add opening stock for at least one branch."}
            )
        stock_serializer = InitialBranchStockSerializer(data=stock_data, many=True)
        stock_serializer.is_valid(raise_exception=True)
        normalized = stock_serializer.validated_data
        branch_ids = [stock["branch_id"] for stock in normalized]
        if len(branch_ids) != len(set(branch_ids)):
            raise serializers.ValidationError(
                {"branch_stocks": "Each branch can appear only once."}
            )
        branches = {
            branch.id: branch
            for branch in Branch.objects.filter(id__in=branch_ids, is_active=True)
        }
        if len(branches) != len(branch_ids):
            raise serializers.ValidationError(
                {"branch_stocks": "Select only active branches."}
            )
        attrs["stocks_for_creation"] = [
            {
                "branch": branches[stock["branch_id"]],
                "quantity_on_hand": stock["quantity_on_hand"],
                "reorder_level": stock["reorder_level"],
                "is_available": stock["is_available"],
            }
            for stock in normalized
        ]
        state = attrs.pop("publication_state")
        attrs["is_active"] = state != "inactive"
        attrs["is_published"] = state == "published"
        if attrs.get("price_type") == Product.PriceType.CONTACT:
            attrs["initial_selling_price"] = 0
            attrs["initial_cost_price"] = 0
        else:
            price_errors = {}
            if attrs.get("initial_selling_price") is None:
                price_errors["initial_selling_price"] = "Selling price is required for fixed-price products."
            if attrs.get("initial_cost_price") is None:
                price_errors["initial_cost_price"] = "Cost price is required for fixed-price products."
            if price_errors:
                raise serializers.ValidationError(price_errors)
        if attrs.get("initial_is_preorder") and not attrs.get("initial_estimated_availability_date"):
            raise serializers.ValidationError({"initial_estimated_availability_date": "An estimated availability date is required for pre-orders."})
        return attrs

    def _unique_slug(self, name):
        base = slugify(name) or "product"
        slug = base
        counter = 2
        while Product.objects.filter(slug=slug).exists():
            slug = f"{base}-{counter}"
            counter += 1
        return slug

    @transaction.atomic
    def create(self, validated_data):
        stocks = validated_data.pop("stocks_for_creation")
        variant_data = {
            "name": validated_data.pop("initial_variant_name"),
            "sku": validated_data.pop("initial_sku"),
            "selling_price": validated_data.pop("initial_selling_price"),
            "cost_price": validated_data.pop("initial_cost_price"),
            "is_preorder": validated_data.pop("initial_is_preorder"),
            "estimated_availability_date": validated_data.pop(
                "initial_estimated_availability_date", None
            ),
        }
        product = Product.objects.create(
            slug=self._unique_slug(validated_data["name"]),
            **validated_data,
        )
        variant = ProductVariant.objects.create(product=product, **variant_data)
        actor = getattr(self.context.get("request"), "user", None)
        for stock in stocks:
            inventory = BranchInventory.objects.create(
                product_variant=variant,
                branch=stock["branch"],
                quantity_on_hand=stock["quantity_on_hand"],
                reorder_level=stock["reorder_level"],
                is_available=stock["is_available"],
            )
            StockMovement.objects.create(
                inventory=inventory,
                movement_type=StockMovement.MovementType.OPENING,
                quantity_on_hand_change=inventory.quantity_on_hand,
                quantity_on_hand_after=inventory.quantity_on_hand,
                quantity_reserved_after=inventory.quantity_reserved,
                note="Opening stock entered during product creation.",
                performed_by=actor if getattr(actor, "is_authenticated", False) else None,
            )
        return product


class ManagementProductInventorySerializer(serializers.ModelSerializer):
    branch_id = serializers.UUIDField(source="branch.id", read_only=True)
    branch_code = serializers.CharField(source="branch.code", read_only=True)
    branch_name = serializers.CharField(source="branch.name", read_only=True)
    branch_is_active = serializers.BooleanField(
        source="branch.is_active", read_only=True
    )
    quantity_available = serializers.IntegerField(read_only=True)

    class Meta:
        model = BranchInventory
        fields = (
            "branch_id",
            "branch_code",
            "branch_name",
            "branch_is_active",
            "quantity_on_hand",
            "quantity_reserved",
            "quantity_available",
            "reorder_level",
            "is_available",
        )


class ManagementProductVariantDetailSerializer(serializers.ModelSerializer):
    stocks = ManagementProductInventorySerializer(
        source="branch_inventory", many=True, read_only=True
    )

    class Meta:
        model = ProductVariant
        fields = (
            "id",
            "name",
            "sku",
            "selling_price",
            "cost_price",
            "is_preorder",
            "estimated_availability_date",
            "is_active",
            "stocks",
        )


class ManagementProductDetailSerializer(serializers.ModelSerializer):
    category_id = serializers.UUIDField(read_only=True)
    category_name = serializers.CharField(source="category.name", read_only=True)
    image_path = serializers.SerializerMethodField()
    publication_state = serializers.SerializerMethodField()
    variants = ManagementProductVariantDetailSerializer(many=True, read_only=True)

    class Meta:
        model = Product
        fields = (
            "id",
            "name",
            "slug",
            "brand",
            "category_id",
            "category_name",
            "description",
            "price_type",
            "image_path",
            "is_featured",
            "is_active",
            "is_published",
            "publication_state",
            "variants",
            "created_at",
            "updated_at",
        )

    def get_image_path(self, product):
        if product.image:
            return product.image.url
        return product.image_path

    def get_publication_state(self, product):
        if not product.is_active:
            return "inactive"
        return "published" if product.is_published else "draft"


class ProductVariantStockInputSerializer(serializers.Serializer):
    branch_id = serializers.UUIDField()
    quantity_on_hand = serializers.IntegerField(min_value=0, max_value=1_000_000)
    reorder_level = serializers.IntegerField(min_value=0, max_value=1_000_000)
    is_available = serializers.BooleanField(default=True)


class ProductVariantInputSerializer(serializers.Serializer):
    id = serializers.UUIDField(required=False)
    name = serializers.CharField(max_length=120)
    sku = serializers.CharField(max_length=80)
    selling_price = serializers.DecimalField(
        max_digits=12, decimal_places=2, min_value=0, required=False, allow_null=True
    )
    cost_price = serializers.DecimalField(
        max_digits=12, decimal_places=2, min_value=0, required=False, allow_null=True
    )
    is_preorder = serializers.BooleanField(default=False)
    estimated_availability_date = serializers.DateField(
        required=False, allow_null=True
    )
    is_active = serializers.BooleanField(default=True)
    stocks = ProductVariantStockInputSerializer(many=True)

    def validate_sku(self, value):
        return value.strip().upper()

    def validate(self, attrs):
        if attrs.get("is_preorder") and not attrs.get("estimated_availability_date"):
            raise serializers.ValidationError({"estimated_availability_date": "Required for pre-order variants."})
        return attrs


class ManagementProductUpdateSerializer(serializers.ModelSerializer):
    category_id = serializers.PrimaryKeyRelatedField(
        source="category",
        queryset=ProductCategory.objects.filter(is_active=True),
    )
    image = RestrictedImageField(required=False, write_only=True)
    publication_state = serializers.ChoiceField(
        choices=("draft", "published", "inactive"), write_only=True
    )
    variants = serializers.CharField(write_only=True)

    class Meta:
        model = Product
        fields = (
            "name",
            "brand",
            "category_id",
            "description",
            "price_type",
            "image",
            "is_featured",
            "publication_state",
            "variants",
        )

    def validate_image(self, image):
        return validate_image_upload(image)

    def validate(self, attrs):
        try:
            raw_variants = json.loads(attrs.pop("variants"))
        except (TypeError, ValueError) as exc:
            raise serializers.ValidationError(
                {"variants": "Variants must be valid JSON."}
            ) from exc
        if not isinstance(raw_variants, list) or not raw_variants:
            raise serializers.ValidationError(
                {"variants": "A product must have at least one variant."}
            )
        serializer = ProductVariantInputSerializer(data=raw_variants, many=True)
        serializer.is_valid(raise_exception=True)
        variants = serializer.validated_data
        price_type = attrs.get("price_type", self.instance.price_type)
        price_errors = []
        for item in variants:
            if price_type == Product.PriceType.CONTACT:
                item["selling_price"] = 0
                item["cost_price"] = 0
            else:
                item_errors = {}
                if item.get("selling_price") is None:
                    item_errors["selling_price"] = "Required for fixed-price products."
                if item.get("cost_price") is None:
                    item_errors["cost_price"] = "Required for fixed-price products."
                price_errors.append(item_errors)
        if price_type != Product.PriceType.CONTACT and any(price_errors):
            raise serializers.ValidationError({"variants": price_errors})
        ids = [item["id"] for item in variants if item.get("id")]
        if len(ids) != len(set(ids)):
            raise serializers.ValidationError(
                {"variants": "Each variant can appear only once."}
            )
        owned_ids = set(
            self.instance.variants.filter(id__in=ids).values_list("id", flat=True)
        )
        if owned_ids != set(ids):
            raise serializers.ValidationError(
                {"variants": "One or more variants do not belong to this product."}
            )
        names = [item["name"].strip().casefold() for item in variants]
        skus = [item["sku"] for item in variants]
        if len(names) != len(set(names)):
            raise serializers.ValidationError(
                {"variants": "Variant names must be unique within a product."}
            )
        if len(skus) != len(set(skus)):
            raise serializers.ValidationError(
                {"variants": "Every SKU must be unique."}
            )
        if ProductVariant.objects.filter(sku__in=skus).exclude(id__in=ids).exists():
            raise serializers.ValidationError(
                {"variants": "One or more SKUs are already in use."}
            )
        active_branch_ids = set(
            Branch.objects.filter(is_active=True).values_list("id", flat=True)
        )
        for item in variants:
            branch_ids = [stock["branch_id"] for stock in item["stocks"]]
            if len(branch_ids) != len(set(branch_ids)):
                raise serializers.ValidationError(
                    {"variants": f"Duplicate branch stock for {item['name']}."}
                )
            if not set(branch_ids).issubset(active_branch_ids):
                raise serializers.ValidationError(
                    {"variants": "Stock can only be assigned to active branches."}
                )
            if item["is_active"] and not branch_ids:
                raise serializers.ValidationError(
                    {"variants": f"Add branch stock for {item['name']}."}
                )
        state = attrs.pop("publication_state")
        attrs["is_active"] = state != "inactive"
        attrs["is_published"] = state == "published"
        attrs["variants_for_update"] = variants
        return attrs

    @transaction.atomic
    def update(self, instance, validated_data):
        variants = validated_data.pop("variants_for_update")
        actor = getattr(self.context.get("request"), "user", None)
        for field, value in validated_data.items():
            setattr(instance, field, value)
        instance.save()
        submitted_ids = []
        for data in variants:
            stocks = data.pop("stocks")
            variant_id = data.pop("id", None)
            if variant_id:
                variant = instance.variants.get(id=variant_id)
                for field, value in data.items():
                    setattr(variant, field, value)
                variant.save()
            else:
                variant = ProductVariant.objects.create(product=instance, **data)
            submitted_ids.append(variant.id)
            for stock in stocks:
                existing = BranchInventory.objects.filter(
                    product_variant=variant, branch_id=stock["branch_id"]
                ).first()
                if (
                    existing
                    and stock["quantity_on_hand"] < existing.quantity_reserved
                ):
                    raise serializers.ValidationError(
                        {
                            "variants": (
                                f"{variant.name} stock cannot be below its "
                                "reserved quantity."
                            )
                        }
                    )
                if existing:
                    previous_on_hand = existing.quantity_on_hand
                    existing.quantity_on_hand = stock["quantity_on_hand"]
                    existing.reorder_level = stock["reorder_level"]
                    existing.is_available = stock["is_available"]
                    existing.save()
                    change = existing.quantity_on_hand - previous_on_hand
                    if change:
                        StockMovement.objects.create(
                            inventory=existing,
                            movement_type=StockMovement.MovementType.ADJUSTMENT,
                            quantity_on_hand_change=change,
                            quantity_on_hand_after=existing.quantity_on_hand,
                            quantity_reserved_after=existing.quantity_reserved,
                            note="Stock balance changed in product management.",
                            performed_by=actor if getattr(actor, "is_authenticated", False) else None,
                        )
                else:
                    inventory = BranchInventory.objects.create(
                        product_variant=variant,
                        branch_id=stock["branch_id"],
                        quantity_on_hand=stock["quantity_on_hand"],
                        reorder_level=stock["reorder_level"],
                        is_available=stock["is_available"],
                    )
                    StockMovement.objects.create(
                        inventory=inventory,
                        movement_type=StockMovement.MovementType.OPENING,
                        quantity_on_hand_change=inventory.quantity_on_hand,
                        quantity_on_hand_after=inventory.quantity_on_hand,
                        quantity_reserved_after=inventory.quantity_reserved,
                        note="Opening stock added to a product variant.",
                        performed_by=actor if getattr(actor, "is_authenticated", False) else None,
                    )
        instance.variants.exclude(id__in=submitted_ids).update(is_active=False)
        return instance


class CustomerCartItemSerializer(serializers.ModelSerializer):
    variant_id = serializers.UUIDField(source="variant.id", read_only=True)
    sku = serializers.CharField(source="variant.sku", read_only=True)
    product_slug = serializers.CharField(source="variant.product.slug", read_only=True)
    product_name = serializers.CharField(source="variant.product.name", read_only=True)
    variant_name = serializers.CharField(source="variant.name", read_only=True)
    unit_price = serializers.DecimalField(
        source="variant.selling_price",
        max_digits=12,
        decimal_places=2,
        read_only=True,
    )
    image_src = serializers.SerializerMethodField()

    class Meta:
        model = CustomerCartItem
        fields = (
            "variant_id",
            "sku",
            "product_slug",
            "product_name",
            "variant_name",
            "unit_price",
            "quantity",
            "image_src",
        )

    def get_image_src(self, item):
        product = item.variant.product
        if product.image:
            return product.image.url
        return product.image_path


class CartLineSerializer(serializers.Serializer):
    variant_id = serializers.UUIDField()
    quantity = serializers.IntegerField(min_value=1, max_value=20)


class CartQuantitySerializer(serializers.Serializer):
    quantity = serializers.IntegerField(min_value=1, max_value=20)


class CartValidationSerializer(serializers.Serializer):
    items = CartLineSerializer(many=True)

    def validate_items(self, items):
        if len(items) > 100:
            raise serializers.ValidationError("A cart cannot exceed 100 lines.")
        variant_ids = [item["variant_id"] for item in items]
        if len(variant_ids) != len(set(variant_ids)):
            raise serializers.ValidationError(
                "Each cart variant can appear only once."
            )
        return items
