from __future__ import annotations

from rest_framework import serializers

from apps.catalog.models import AddOn, Category, Product, ProductAddOn
from apps.catalog.search import MAX_PRICE_FILTER, MAX_SEARCH_LENGTH, SORT_CHOICES


class CategoryPublicSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = Category
        # ``parent_id`` lets the frontend rebuild the category tree without
        # exposing the whole parent object in every product row.
        fields = ("id", "name", "slug", "description", "parent_id", "image_url")

    def get_image_url(self, obj: Category) -> str | None:
        if obj.webp_image:
            return obj.webp_image.url
        if obj.image:
            return obj.image.url
        return None


class ProductAddOnPublicSerializer(serializers.ModelSerializer):
    addon_id = serializers.IntegerField(source="addon.id")
    name = serializers.CharField(source="addon.name")
    price = serializers.IntegerField(source="addon.price")

    class Meta:
        model = ProductAddOn
        fields = ("addon_id", "name", "price", "min_quantity", "max_quantity")


class ProductDetailPublicSerializer(serializers.ModelSerializer):
    category = CategoryPublicSerializer(read_only=True)
    image_url = serializers.SerializerMethodField()
    addons = ProductAddOnPublicSerializer(source="addon_links", many=True)
    discount_percent = serializers.IntegerField(read_only=True)
    is_discounted = serializers.BooleanField(read_only=True)

    class Meta:
        model = Product
        fields = (
            "id",
            "name",
            "slug",
            "description",
            "price",
            "compare_at_price",
            "discount_percent",
            "is_discounted",
            "status",
            "is_main_dish",
            "prep_time_minutes",
            "image_url",
            "category",
            "addons",
        )

    def get_image_url(self, obj: Product) -> str | None:
        if obj.webp_image:
            return obj.webp_image.url
        if obj.image:
            return obj.image.url
        return None


# ---------------------------------------------------------------------------
# Product discovery (listing + autocomplete)
# ---------------------------------------------------------------------------
class ProductSummaryPublicSerializer(serializers.ModelSerializer):
    """Compact public product row used by the search/listing endpoint."""

    category = CategoryPublicSerializer(read_only=True)
    image_url = serializers.SerializerMethodField()
    discount_percent = serializers.IntegerField(read_only=True)
    is_discounted = serializers.BooleanField(read_only=True)

    class Meta:
        model = Product
        fields = (
            "id",
            "name",
            "slug",
            "description",
            "price",
            "compare_at_price",
            "discount_percent",
            "is_discounted",
            "status",
            "is_main_dish",
            "prep_time_minutes",
            "image_url",
            "category",
        )
        read_only_fields = fields

    def get_image_url(self, obj: Product) -> str | None:
        if obj.webp_image:
            return obj.webp_image.url
        if obj.image:
            return obj.image.url
        return None


class ProductSuggestionPublicSerializer(serializers.ModelSerializer):
    """Minimal payload for autocomplete; must match suggest_public_products().only()."""

    image_url = serializers.SerializerMethodField()
    discount_percent = serializers.IntegerField(read_only=True)

    class Meta:
        model = Product
        fields = (
            "id",
            "name",
            "slug",
            "price",
            "compare_at_price",
            "discount_percent",
            "status",
            "image_url",
        )
        read_only_fields = fields

    def get_image_url(self, obj: Product) -> str | None:
        if obj.webp_image:
            return obj.webp_image.url
        if obj.image:
            return obj.image.url
        return None


class ProductSearchQuerySerializer(serializers.Serializer):
    """Validates GET query parameters for the public product listing."""

    q = serializers.CharField(
        required=False,
        allow_blank=True,
        trim_whitespace=True,
        max_length=MAX_SEARCH_LENGTH,
    )
    category = serializers.SlugField(
        required=False, allow_blank=True, max_length=128
    )
    category_id = serializers.IntegerField(required=False, min_value=1)
    min_price = serializers.IntegerField(
        required=False, min_value=0, max_value=MAX_PRICE_FILTER
    )
    max_price = serializers.IntegerField(
        required=False, min_value=0, max_value=MAX_PRICE_FILTER
    )
    available = serializers.BooleanField(required=False)
    discount = serializers.BooleanField(required=False)
    include_subcategories = serializers.BooleanField(required=False, default=True)
    is_main_dish = serializers.BooleanField(required=False)
    sort = serializers.ChoiceField(choices=SORT_CHOICES, required=False)

    def validate(self, attrs: dict) -> dict:
        min_price = attrs.get("min_price")
        max_price = attrs.get("max_price")
        if min_price is not None and max_price is not None and min_price > max_price:
            raise serializers.ValidationError(
                {"max_price": "بیشترین قیمت نباید کمتر از کمترین قیمت باشد."}
            )

        if not attrs.get("category"):
            attrs.pop("category", None)

        return attrs


class ProductSuggestionQuerySerializer(serializers.Serializer):
    """Validates GET query parameters for autocomplete."""

    q = serializers.CharField(
        required=False,
        allow_blank=True,
        trim_whitespace=True,
        max_length=MAX_SEARCH_LENGTH,
    )
    limit = serializers.IntegerField(required=False, min_value=1, max_value=1000)


# ---------------------------------------------------------------------------
# OpenAPI response envelopes (documentation only)
# ---------------------------------------------------------------------------
class ProductListResponseSerializer(serializers.Serializer):
    count = serializers.IntegerField()
    next = serializers.CharField(allow_null=True)
    previous = serializers.CharField(allow_null=True)
    results = ProductSummaryPublicSerializer(many=True)


class ProductSuggestionListResponseSerializer(serializers.Serializer):
    results = ProductSuggestionPublicSerializer(many=True)
    did_you_mean = serializers.CharField(allow_null=True, required=False)


# ---------------------------------------------------------------------------
# Menu / lucky wheel (documentation of cached dict payloads)
# ---------------------------------------------------------------------------
class MenuProductSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    slug = serializers.SlugField()
    description = serializers.CharField()
    price = serializers.IntegerField()
    status = serializers.ChoiceField(choices=Product.Status.choices)
    is_main_dish = serializers.BooleanField()
    prep_time_minutes = serializers.IntegerField()
    image_url = serializers.CharField(allow_null=True)


class MenuCategorySerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    slug = serializers.SlugField()
    description = serializers.CharField()
    image_url = serializers.CharField(allow_null=True)
    products = MenuProductSerializer(many=True)


class MenuResponseSerializer(serializers.Serializer):
    categories = MenuCategorySerializer(many=True)


class LuckyWheelProductSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    slug = serializers.SlugField()
    price = serializers.IntegerField()
    category_id = serializers.IntegerField()
    image_url = serializers.CharField(allow_null=True)


class LuckyWheelResponseSerializer(serializers.Serializer):
    products = LuckyWheelProductSerializer(many=True)