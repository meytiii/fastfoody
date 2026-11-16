from __future__ import annotations

from django.db import models

from common.models import BaseModel


class Category(BaseModel):
    name = models.CharField(max_length=128)
    slug = models.SlugField(max_length=128, db_index=True)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to="catalog/categories/", blank=True, null=True)
    webp_image = models.ImageField(
        upload_to="catalog/categories/webp/", blank=True, null=True
    )
    display_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta(BaseModel.Meta):
        ordering = ("display_order", "name")
        constraints = [
            models.UniqueConstraint(
                fields=["slug"],
                condition=models.Q(deleted_at__isnull=True),
                name="unique_alive_category_slug",
            ),
        ]
        verbose_name = "Category"
        verbose_name_plural = "Categories"

    def __str__(self) -> str:
        return self.name


class AddOn(BaseModel):
    name = models.CharField(max_length=128)
    price = models.PositiveIntegerField(default=0)
    is_available = models.BooleanField(default=True, db_index=True)

    class Meta(BaseModel.Meta):
        ordering = ("name",)
        verbose_name = "Add-on"
        verbose_name_plural = "Add-ons"

    def __str__(self) -> str:
        return self.name


class Product(BaseModel):
    class Status(models.TextChoices):
        AVAILABLE = "AVAILABLE", "Available"
        OUT_OF_STOCK = "OUT_OF_STOCK", "Out of stock"
        HIDDEN = "HIDDEN", "Hidden"

    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name="products",
    )
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, db_index=True)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to="catalog/products/", blank=True, null=True)
    webp_image = models.ImageField(
        upload_to="catalog/products/webp/", blank=True, null=True
    )
    price = models.PositiveIntegerField()
    status = models.CharField(
        max_length=16,
        choices=Status.choices,
        default=Status.AVAILABLE,
        db_index=True,
    )
    is_main_dish = models.BooleanField(default=True, db_index=True)
    prep_time_minutes = models.PositiveSmallIntegerField(default=0)
    display_order = models.PositiveIntegerField(default=0)

    addons = models.ManyToManyField(
        AddOn,
        through="catalog.ProductAddOn",
        related_name="products",
    )

    class Meta(BaseModel.Meta):
        ordering = ("display_order", "name")
        constraints = [
            models.UniqueConstraint(
                fields=["slug"],
                condition=models.Q(deleted_at__isnull=True),
                name="unique_alive_product_slug",
            ),
        ]
        verbose_name = "Product"
        verbose_name_plural = "Products"

    def __str__(self) -> str:
        return self.name


class ProductAddOn(BaseModel):
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="addon_links",
    )
    addon = models.ForeignKey(
        AddOn,
        on_delete=models.CASCADE,
        related_name="product_links",
    )
    min_quantity = models.PositiveSmallIntegerField(default=0)
    max_quantity = models.PositiveSmallIntegerField(default=5)

    class Meta(BaseModel.Meta):
        ordering = ("addon__name",)
        constraints = [
            models.UniqueConstraint(
                fields=["product", "addon"],
                condition=models.Q(deleted_at__isnull=True),
                name="unique_alive_product_addon",
            ),
            models.CheckConstraint(
                check=models.Q(min_quantity__lte=models.F("max_quantity")),
                name="product_addon_min_lte_max",
            ),
        ]
        verbose_name = "Product Add-on"
        verbose_name_plural = "Product Add-ons"

    def __str__(self) -> str:
        return f"{self.product.name} + {self.addon.name}"