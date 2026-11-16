from __future__ import annotations

from rest_framework import serializers

from apps.catalog.models import AddOn, Category, Product, ProductAddOn


class CategoryPublicSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ("id", "name", "slug", "description", "image_url")

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

    class Meta:
        model = Product
        fields = (
            "id",
            "name",
            "slug",
            "description",
            "price",
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