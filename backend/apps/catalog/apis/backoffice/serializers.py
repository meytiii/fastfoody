from __future__ import annotations

from typing import Any

from rest_framework import serializers

from apps.catalog.models import AddOn, Category, Product, ProductAddOn


# ---------------------------------------------------------------------------
# Category
# ---------------------------------------------------------------------------
class CategoryReadSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()
    webp_image_url = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = (
            "id",
            "name",
            "slug",
            "description",
            "image_url",
            "webp_image_url",
            "display_order",
            "is_active",
            "created_at",
            "updated_at",
        )

    def get_image_url(self, obj: Category) -> str | None:
        return obj.image.url if obj.image else None

    def get_webp_image_url(self, obj: Category) -> str | None:
        return obj.webp_image.url if obj.webp_image else None


class CategoryWriteSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=128)
    slug = serializers.SlugField(max_length=128)
    description = serializers.CharField(
        required=False, allow_blank=True, default=""
    )
    display_order = serializers.IntegerField(min_value=0, default=0)
    is_active = serializers.BooleanField(default=True)


class CategoryUpdateSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=128, required=False)
    slug = serializers.SlugField(max_length=128, required=False)
    description = serializers.CharField(required=False, allow_blank=True)
    display_order = serializers.IntegerField(min_value=0, required=False)
    is_active = serializers.BooleanField(required=False)


# ---------------------------------------------------------------------------
# AddOn
# ---------------------------------------------------------------------------
class AddOnSerializer(serializers.ModelSerializer):
    class Meta:
        model = AddOn
        fields = ("id", "name", "price", "is_available", "created_at", "updated_at")
        read_only_fields = ("id", "created_at", "updated_at")


class AddOnWriteSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=128)
    price = serializers.IntegerField(min_value=0, default=0)
    is_available = serializers.BooleanField(default=True)


class AddOnUpdateSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=128, required=False)
    price = serializers.IntegerField(min_value=0, required=False)
    is_available = serializers.BooleanField(required=False)


# ---------------------------------------------------------------------------
# Product
# ---------------------------------------------------------------------------
class AddonLinkSerializer(serializers.Serializer):
    addon_id = serializers.IntegerField()
    min_quantity = serializers.IntegerField(min_value=0, default=0)
    max_quantity = serializers.IntegerField(min_value=0, default=5)

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        if attrs["min_quantity"] > attrs["max_quantity"]:
            raise serializers.ValidationError(
                {"max_quantity": "بیشینه نباید کمتر از کمینه باشد."}
            )
        return attrs


class ProductReadSerializer(serializers.ModelSerializer):
    category = CategoryReadSerializer(read_only=True)
    image_url = serializers.SerializerMethodField()
    webp_image_url = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = (
            "id",
            "category",
            "name",
            "slug",
            "description",
            "image_url",
            "webp_image_url",
            "price",
            "status",
            "is_main_dish",
            "prep_time_minutes",
            "display_order",
            "created_at",
            "updated_at",
        )

    def get_image_url(self, obj: Product) -> str | None:
        return obj.image.url if obj.image else None

    def get_webp_image_url(self, obj: Product) -> str | None:
        return obj.webp_image.url if obj.webp_image else None


class ProductAddOnReadSerializer(serializers.ModelSerializer):
    addon_id = serializers.IntegerField(source="addon.id")
    name = serializers.CharField(source="addon.name")
    price = serializers.IntegerField(source="addon.price")
    is_available = serializers.BooleanField(source="addon.is_available")

    class Meta:
        model = ProductAddOn
        fields = (
            "addon_id",
            "name",
            "price",
            "is_available",
            "min_quantity",
            "max_quantity",
        )


class ProductDetailReadSerializer(ProductReadSerializer):
    addons = ProductAddOnReadSerializer(source="addon_links", many=True)

    class Meta(ProductReadSerializer.Meta):
        fields = ProductReadSerializer.Meta.fields + ("addons",)


class ProductWriteSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=255)
    slug = serializers.SlugField(max_length=255)
    category_id = serializers.IntegerField()
    description = serializers.CharField(
        required=False, allow_blank=True, default=""
    )
    price = serializers.IntegerField(min_value=0)
    status = serializers.ChoiceField(
        choices=Product.Status.choices, default=Product.Status.AVAILABLE
    )
    is_main_dish = serializers.BooleanField(default=True)
    prep_time_minutes = serializers.IntegerField(min_value=0, default=0)
    display_order = serializers.IntegerField(min_value=0, default=0)
    addons = AddonLinkSerializer(many=True, required=False)


class ProductUpdateSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=255, required=False)
    slug = serializers.SlugField(max_length=255, required=False)
    category_id = serializers.IntegerField(required=False)
    description = serializers.CharField(required=False, allow_blank=True)
    price = serializers.IntegerField(min_value=0, required=False)
    status = serializers.ChoiceField(choices=Product.Status.choices, required=False)
    is_main_dish = serializers.BooleanField(required=False)
    prep_time_minutes = serializers.IntegerField(min_value=0, required=False)
    display_order = serializers.IntegerField(min_value=0, required=False)
    addons = AddonLinkSerializer(many=True, required=False)


class ImageUploadSerializer(serializers.Serializer):
    image = serializers.ImageField()

    def validate_image(self, value):
        max_bytes = 10 * 1024 * 1024
        if value.size > max_bytes:
            raise serializers.ValidationError("حجم فایل نباید بیش از ۱۰ مگابایت باشد.")
        return value


class AddonLinksWriteSerializer(serializers.Serializer):
    addons = AddonLinkSerializer(many=True)