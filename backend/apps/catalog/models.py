from django.db import models
from django.core.exceptions import ValidationError
from common.models import BaseModel
from common.utils import compress_image_to_webp


class Category(BaseModel):
    name = models.CharField(max_length=120)
    slug = models.SlugField(max_length=140, db_index=True)
    icon = models.ImageField(upload_to="catalog/categories/", null=True, blank=True)
    display_order = models.PositiveSmallIntegerField(default=0, db_index=True)
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        db_table = "catalog_category"
        ordering = ["display_order", "name"]
        constraints = [
            models.UniqueConstraint(
                fields=["slug"],
                condition=models.Q(deleted_at__isnull=True),
                name="uq_category_slug_active",
            )
        ]

    def __str__(self):
        return self.name


class Product(BaseModel):
    class Status(models.TextChoices):
        AVAILABLE = "available", "موجود"
        OUT_OF_STOCK = "out_of_stock", "تموم شده (ناموجود موقت)"
        HIDDEN = "hidden", "عدم نمایش در منو"

    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name="products")
    name = models.CharField(max_length=200, db_index=True)
    slug = models.SlugField(max_length=220, db_index=True)
    description = models.TextField(blank=True)
    ingredients = models.CharField(
        max_length=300,
        blank=True,
        help_text="مخلفات با کاما جدا شوند (مثلاً: ژامبون، قارچ، پنیر گودا)",
    )
    image = models.ImageField(upload_to="catalog/products/", null=True, blank=True)
    
    price = models.PositiveIntegerField(help_text="قیمت به تومان")
    discount_price = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="قیمت با تخفیف به تومان (در صورت وجود)",
    )
    prep_time_minutes = models.PositiveSmallIntegerField(
        default=20,
        help_text="مدت زمان آماده‌سازی این غذا به دقیقه",
    )
    
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.AVAILABLE,
        db_index=True,
    )
    is_main_dish = models.BooleanField(
        default=True,
        db_index=True,
        help_text="True: غذای اصلی (وارد گردونه شانس می‌شود) | False: پیش‌غذا/نوشیدنی (پیشنهاد موقع تکمیل خرید)",
    )
    display_order = models.PositiveSmallIntegerField(default=0, db_index=True)

    class Meta:
        db_table = "catalog_product"
        ordering = ["display_order", "-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["slug"],
                condition=models.Q(deleted_at__isnull=True),
                name="uq_product_slug_active",
            )
        ]

    @property
    def final_price(self) -> int:
        if self.discount_price and 0 < self.discount_price < self.price:
            return self.discount_price
        return self.price

    def clean(self):
        if self.discount_price and self.discount_price >= self.price:
            raise ValidationError("قیمت با تخفیف باید کمتر از قیمت اصلی باشد.")

    def save(self, *args, **kwargs):
        if self.image and not str(self.image.name).endswith(".webp"):
            self.image = compress_image_to_webp(self.image, max_width=800)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} ({self.get_status_display()})"


class AddOn(BaseModel):
    """افزودنی‌های سراسری (مثل پنیر اضافه، نان اضافه، سس مخصوص)"""
    name = models.CharField(max_length=120)
    price = models.PositiveIntegerField(help_text="قیمت هر واحد افزودنی به تومان")
    is_available = models.BooleanField(
        default=True,
        db_index=True,
        help_text="با غیرفعال کردن این تیک، این افزودنی از روی تمام محصولات سایت موقتاً ناموجود می‌شود.",
    )

    class Meta:
        db_table = "catalog_addon"
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} (+{self.price:,} تومان)"


class ProductAddOn(BaseModel):
    """جدول واسط برای اتصال افزودنی‌ها به هر محصول با قوانین حداقل/حداکثر انتخاب"""
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="product_addons")
    addon = models.ForeignKey(AddOn, on_delete=models.CASCADE, related_name="product_links")
    min_quantity = models.PositiveSmallIntegerField(default=0, help_text="۰ یعنی اختیاری")
    max_quantity = models.PositiveSmallIntegerField(default=5, help_text="حداکثر تعداد قابل انتخاب برای یک غذا")
    display_order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        db_table = "catalog_product_addon"
        ordering = ["display_order", "id"]
        constraints = [
            models.UniqueConstraint(
                fields=["product", "addon"],
                condition=models.Q(deleted_at__isnull=True),
                name="uq_product_addon_active",
            )
        ]

    def __str__(self):
        return f"{self.product.name} -> {self.addon.name} (Max: {self.max_quantity})"