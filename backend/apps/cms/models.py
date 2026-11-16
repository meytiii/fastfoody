from datetime import time
from django.db import models
from common.models import BaseModel
from common.utils import compress_image_to_webp


class RestaurantSettings(BaseModel):
    """
    مدل Singleton برای تنظیمات عملیاتی که بک‌اند با آن‌ها محاسبه انجام می‌دهد.
    همیشه فقط رکورد اول آن خوانده و آپدیت می‌شود.
    """
    open_time = models.TimeField(default=time(11, 0), help_text="ساعت شروع سفارش‌گیری (مثلاً 11:00)")
    close_time = models.TimeField(default=time(1, 0), help_text="ساعت پایان سفارش‌گیری (مثلاً 01:00 بامداد)")
    is_temporarily_closed = models.BooleanField(
        default=False,
        help_text="دکمه اضطراری توقف موقت سفارش‌گیری توسط مدیر",
    )
    closed_message = models.CharField(
        max_length=255,
        default="در حال حاضر سفارش‌گیری آنلاین غیرفعال است.",
    )

    in_zone_delivery_fee = models.PositiveIntegerField(default=50000, help_text="هزینه پیک داخل شهر (تومان)")
    out_zone_delivery_fee = models.PositiveIntegerField(default=100000, help_text="هزینه پیک خارج از شهر (تومان)")
    prep_time_buffer_minutes = models.PositiveSmallIntegerField(
        default=5,
        help_text="تلورانس اضافه شونده به بیشترین زمان پخت آیتم‌های سبد خرید (دقیقه)",
    )
    owner_notification_phone = models.CharField(
        max_length=11,
        default="09120000000",
        help_text="شماره موبایل صاحب رستوران جهت دریافت پیامک ثبت سفارش جدید",
    )

    class Meta:
        db_table = "cms_restaurant_settings"

    @classmethod
    def load(cls) -> "RestaurantSettings":
        obj = cls.objects.first()
        if not obj:
            obj = cls.objects.create()
        return obj

    def __str__(self):
        return "تنظیمات عملیاتی رستوران"


class SiteSection(BaseModel):
    """مدیریت محتوای ظاهری سایت توسط صاحب رستوران بدون نیاز به تغییر کد"""
    HEADER = "header"
    HERO = "hero"
    ANNOUNCEMENT = "announcement"
    LUCKY_WHEEL = "lucky_wheel"
    ABOUT_US = "about_us"
    FOOTER = "footer"

    ALLOWED_KEYS = (HEADER, HERO, ANNOUNCEMENT, LUCKY_WHEEL, ABOUT_US, FOOTER)

    key = models.CharField(max_length=64, db_index=True)
    content = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = "cms_site_section"
        constraints = [
            models.UniqueConstraint(
                fields=["key"],
                condition=models.Q(deleted_at__isnull=True),
                name="uq_sitesection_key_active",
            )
        ]

    def __str__(self):
        return f"Section: {self.key}"


class MediaAsset(BaseModel):
    """کتابخانه فایل و تصاویر CMS با تبدیل خودکار به WebP"""
    title = models.CharField(max_length=150, blank=True)
    file = models.ImageField(upload_to="cms/assets/")

    class Meta:
        db_table = "cms_media_asset"
        ordering = ["-created_at"]

    def save(self, *args, **kwargs):
        if self.file and not str(self.file.name).endswith(".webp"):
            self.file = compress_image_to_webp(self.file, max_width=1600)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title or self.file.name