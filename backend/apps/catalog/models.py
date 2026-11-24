from __future__ import annotations

from django.db import models

from common.models import BaseModel


class Category(BaseModel):
    parent = models.ForeignKey(
        "self",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="children",
        help_text="Optional parent category; the catalog supports one nesting level "
        "for navigation but the model allows any depth.",
    )
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
            # A category can never be its own parent. Deeper cycles are rejected
            # by catalog.services (the check needs an ancestor walk).
            models.CheckConstraint(
                check=~models.Q(pk=models.F("parent_id")),
                name="category_parent_not_self",
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
    #: Effective selling price in toman. Orders snapshot this exact value, so a
    #: discount never changes order totals retroactively.
    price = models.PositiveIntegerField()
    #: Original (pre-discount) price. ``None`` means the product is not discounted;
    #: when set it must be strictly greater than ``price`` (enforced by a DB
    #: constraint and by the backoffice services).
    compare_at_price = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Original price before discount; leave empty when not discounted.",
    )
    #: Optional stock count. ``None`` means stock is not tracked and availability
    #: is governed by ``status`` only (the historical behaviour).
    stock_quantity = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Units left in stock; leave empty when stock is not tracked.",
    )
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
            models.CheckConstraint(
                check=models.Q(compare_at_price__isnull=True)
                | models.Q(compare_at_price__gt=models.F("price")),
                name="product_compare_at_price_gt_price",
            ),
        ]
        indexes = [
            # Price sorting/filtering on the discovery endpoint.
            models.Index(fields=["price"], name="catalog_product_price_idx"),
            # Category listing combined with the status visibility filter.
            models.Index(
                fields=["category", "status"],
                name="catalog_product_cat_status_idx",
            ),
        ]
        verbose_name = "Product"
        verbose_name_plural = "Products"

    def __str__(self) -> str:
        return self.name

    @property
    def is_discounted(self) -> bool:
        """True when a valid original price above the selling price is set."""
        return self.compare_at_price is not None and self.compare_at_price > self.price

    @property
    def discount_percent(self) -> int:
        """Rounded discount percentage; 0 when the product is not discounted."""
        if not self.is_discounted:
            return 0
        assert self.compare_at_price is not None
        return round((self.compare_at_price - self.price) * 100 / self.compare_at_price)

    @property
    def is_in_stock(self) -> bool:
        """
        Purchasability derived from both the status flag and counted stock.

        ``OUT_OF_STOCK``/``HIDDEN`` are never in stock. When ``stock_quantity`` is
        ``None`` the product is treated as unlimited (backward compatible).
        """
        if self.status != self.Status.AVAILABLE:
            return False
        return self.stock_quantity is None or self.stock_quantity > 0


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