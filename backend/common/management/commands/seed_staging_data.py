from __future__ import annotations

from datetime import time
from typing import Any

from decouple import config
from django.core.cache import cache
from django.core.management.base import BaseCommand
from django.db import transaction

from apps.accounts.models import Customer, CustomerAddress
from apps.catalog.models import AddOn, Category, Product, ProductAddOn
from apps.cms.models import RestaurantSettings, SiteSection
from apps.orders.models import PromoCode

ADMIN_PHONE = "09120000000"
SAMPLE_CUSTOMER_PHONE = "09121234567"

CATEGORY_ROWS: tuple[dict[str, Any], ...] = (
    {"name": "پیتزا", "slug": "pizza", "display_order": 1},
    {"name": "برگر", "slug": "burger", "display_order": 2},
    {"name": "سوخاری", "slug": "fried-chicken", "display_order": 3},
    {"name": "پیش‌غذا", "slug": "appetizer", "display_order": 4},
    {"name": "نوشیدنی", "slug": "drink", "display_order": 5},
)

ADDON_ROWS: tuple[dict[str, Any], ...] = (
    {"key": "cheese", "name": "پنیر اضافه", "price": 20_000},
    {"key": "sauce", "name": "سس مخصوص", "price": 12_000},
    {"key": "garlic_bread", "name": "نان سیر", "price": 25_000},
)

PRODUCT_ROWS: tuple[dict[str, Any], ...] = (
    # Pizzas
    {
        "category": "pizza",
        "name": "پیتزا مارگاریتا",
        "slug": "margherita-pizza",
        "description": "پیتزا با سس گوجه، پنیر موزارلا و ریحان تازه",
        "price": 185_000,
        "prep_time_minutes": 18,
        "display_order": 1,
    },
    {
        "category": "pizza",
        "name": "پیتزا پپرونی",
        "slug": "pepperoni-pizza",
        "description": "پیتزا با پپرونی تند و پنیر موزارلا",
        "price": 235_000,
        "compare_at_price": 265_000,
        "prep_time_minutes": 20,
        "display_order": 2,
    },
    {
        "category": "pizza",
        "name": "پیتزا مخصوص",
        "slug": "special-pizza",
        "description": "ترکیب گوشت، مرغ، قارچ، فلفل دلمه و پنیر",
        "price": 275_000,
        "prep_time_minutes": 22,
        "display_order": 3,
    },
    {
        "category": "pizza",
        "name": "پیتزا سبزیجات",
        "slug": "veggie-pizza",
        "description": "قارچ، فلفل دلمه، ذرت، زیتون و گوجه",
        "price": 205_000,
        "prep_time_minutes": 18,
        "display_order": 4,
    },
    # Burgers
    {
        "category": "burger",
        "name": "همبرگر کلاسیک",
        "slug": "classic-burger",
        "description": "همبرگر گوشت دست‌ساز با کاهو، گوجه و سس مخصوص",
        "price": 165_000,
        "compare_at_price": 185_000,
        "prep_time_minutes": 12,
        "display_order": 1,
    },
    {
        "category": "burger",
        "name": "چیزبرگر دوبل",
        "slug": "double-cheeseburger",
        "description": "دو لایه گوشت و پنیر چدار ذوب‌شده",
        "price": 225_000,
        "prep_time_minutes": 15,
        "display_order": 2,
    },
    {
        "category": "burger",
        "name": "برگر قارچ و پنیر",
        "slug": "mushroom-cheese-burger",
        "description": "گوشت دست‌ساز، قارچ سوتی و پنیر گودا",
        "price": 195_000,
        "prep_time_minutes": 14,
        "display_order": 3,
    },
    # Fried chicken
    {
        "category": "fried-chicken",
        "name": "مرغ سوخاری دو تکه",
        "slug": "two-piece-fried-chicken",
        "description": "دو تکه مرغ سوخاری با سیب‌زمینی و سس",
        "price": 245_000,
        "prep_time_minutes": 16,
        "display_order": 1,
    },
    {
        "category": "fried-chicken",
        "name": "مرغ سوخاری تک",
        "slug": "one-piece-fried-chicken",
        "description": "یک تکه مرغ سوخاری تازه و ترد",
        "price": 145_000,
        "status": Product.Status.OUT_OF_STOCK,
        "prep_time_minutes": 14,
        "display_order": 2,
    },
    {
        "category": "fried-chicken",
        "name": "فیله استریپس",
        "slug": "chicken-strips",
        "description": "فیله مرغ سوخاری در اندازه‌های کوچک با سس",
        "price": 185_000,
        "prep_time_minutes": 13,
        "display_order": 3,
    },
    # Appetizers / sides
    {
        "category": "appetizer",
        "name": "سیب‌زمینی سرخ‌کرده",
        "slug": "french-fries",
        "description": "سیب‌زمینی تازه با نمک و ادویه مخصوص",
        "price": 75_000,
        "is_main_dish": False,
        "prep_time_minutes": 8,
        "display_order": 1,
    },
    {
        "category": "appetizer",
        "name": "ناگت مرغ",
        "slug": "chicken-nuggets",
        "description": "شش عدد ناگت مرغ با سس مخصوص",
        "price": 95_000,
        "is_main_dish": False,
        "prep_time_minutes": 9,
        "display_order": 2,
    },
    {
        "category": "appetizer",
        "name": "حلقه پیاز",
        "slug": "onion-rings",
        "description": "حلقه‌های پیاز سوخاری ترد",
        "price": 85_000,
        "is_main_dish": False,
        "prep_time_minutes": 9,
        "display_order": 3,
    },
    # Drinks
    {
        "category": "drink",
        "name": "کوکاکولا",
        "slug": "coca-cola",
        "description": "نوشابه گازدار ۳۰۰ میلی‌لیتری",
        "price": 30_000,
        "is_main_dish": False,
        "prep_time_minutes": 0,
        "display_order": 1,
    },
    {
        "category": "drink",
        "name": "دوغ سنتی",
        "slug": "traditional-doogh",
        "description": "دوغ خانگی خنک با نعناع",
        "price": 28_000,
        "is_main_dish": False,
        "prep_time_minutes": 0,
        "display_order": 2,
    },
    {
        "category": "drink",
        "name": "آب معدنی",
        "slug": "mineral-water",
        "description": "آب معدنی ۵۰۰ میلی‌لیتری",
        "price": 15_000,
        "is_main_dish": False,
        "prep_time_minutes": 0,
        "display_order": 3,
    },
)

ADDON_LINKS: tuple[dict[str, Any], ...] = (
    {
        "addon": "cheese",
        "categories": ("pizza", "burger"),
        "min_quantity": 0,
        "max_quantity": 3,
    },
    {
        "addon": "sauce",
        "categories": ("pizza", "burger", "fried-chicken"),
        "min_quantity": 0,
        "max_quantity": 2,
    },
    {
        "addon": "garlic_bread",
        "categories": ("pizza",),
        "min_quantity": 0,
        "max_quantity": 1,
    },
)

SITE_SECTION_CONTENT: dict[str, dict[str, Any]] = {
    "hero": {
        "title": "طعم واقعی فست‌فود",
        "subtitle": "تازه، داغ و سریع درِ خانه شما",
        "cta_text": "سفارش آنلاین",
        "cta_link": "/menu",
    },
    "header": {
        "restaurant_name": "فست‌فود شهر",
        "tagline": "سریع، تازه، خوشمزه",
        "phone": "02112345678",
    },
    "footer": {
        "copyright_text": "© فست‌فود شهر",
        "address": "تهران، خیابان ولیعصر، پلاک ۱۲",
        "phone": "02112345678",
        "working_hours_text": "هر روز ۱۱:۰۰ تا ۰۱:۰۰",
    },
    "announcement": {
        "text": "ارسال رایگان برای سفارش‌های بالای ۵۰۰ هزار تومان",
        "is_active": False,
        "link": "",
    },
    "lucky_wheel": {
        "title": "گردونه شانس",
        "subtitle": "با هر سفارش یک شانس قرعه‌کشی",
        "is_active": True,
    },
    "about_us": {
        "title": "درباره ما",
        "body": (
            "فست‌فود شهر از سال ۱۳۹۰ با مواد اولیه تازه و دستورهای اختصاصی "
            "در خدمت شماست."
        ),
        "image_url": "",
    },
}

PROMO_ROWS: tuple[dict[str, Any], ...] = (
    {
        "code": "WELCOME20",
        "discount_type": PromoCode.DiscountType.PERCENTAGE,
        "discount_value": 20,
        "max_discount_amount": 60_000,
        "first_order_only": True,
        "max_uses_per_customer": 1,
    },
    {
        "code": "FAST30",
        "discount_type": PromoCode.DiscountType.FIXED,
        "discount_value": 30_000,
        "max_uses_per_customer": 1,
    },
)

ADDRESS_ROWS: tuple[dict[str, Any], ...] = (
    {
        "title": "خانه",
        "address_text": "تهران، سعادت‌آباد، بلوار دریا، کوچه ۱۲، پلاک ۸",
        "recipient_name": "مشتری نمونه",
        "recipient_phone": SAMPLE_CUSTOMER_PHONE,
        "is_out_of_zone": False,
    },
    {
        "title": "محل کار",
        "address_text": "تهران، ونک، خیابان گاندی، ساختمان اداری آفتاب، طبقه ۳",
        "recipient_name": "مشتری نمونه",
        "recipient_phone": SAMPLE_CUSTOMER_PHONE,
        "is_out_of_zone": True,
    },
)


class Command(BaseCommand):
    help = "Seed idempotent pre-production/staging data."

    @transaction.atomic
    def handle(self, *args: Any, **options: Any) -> None:
        created: dict[str, int] = {}

        # The CMS migration seeds pk=1 with model defaults, so this must update
        # rather than only create: staging needs the exact fees below even when
        # the row already exists.
        _, was_created = RestaurantSettings.objects.update_or_create(
            pk=1,
            defaults={
                "open_time": time(11, 0),
                "close_time": time(1, 0),
                "is_temporarily_closed": False,
                "in_zone_delivery_fee": 50_000,
                "out_zone_delivery_fee": 100_000,
                "packaging_fee": 15_000,
                "min_delivery_order_amount": 150_000,
                "prep_time_buffer_minutes": 5,
            },
        )
        created["restaurant_settings"] = int(was_created)

        created["site_sections"] = 0
        for key, content in SITE_SECTION_CONTENT.items():
            merged = {**SiteSection.get_default_content(key), **content}
            _, was_created = SiteSection.objects.get_or_create(
                key=key, defaults={"content": merged}
            )
            created["site_sections"] += int(was_created)

        categories: dict[str, Category] = {}
        created["categories"] = 0
        for row in CATEGORY_ROWS:
            category, was_created = Category.objects.get_or_create(
                slug=row["slug"],
                defaults={
                    "name": row["name"],
                    "display_order": row["display_order"],
                },
            )
            categories[row["slug"]] = category
            created["categories"] += int(was_created)

        addons: dict[str, AddOn] = {}
        created["addons"] = 0
        for row in ADDON_ROWS:
            addon, was_created = AddOn.objects.get_or_create(
                name=row["name"],
                defaults={"price": row["price"]},
            )
            addons[row["key"]] = addon
            created["addons"] += int(was_created)

        created["products"] = 0
        for row in PRODUCT_ROWS:
            data = dict(row)
            category_slug = data.pop("category")
            slug = data.pop("slug")
            _, was_created = Product.objects.get_or_create(
                slug=slug,
                defaults={**data, "category": categories[category_slug]},
            )
            created["products"] += int(was_created)

        created["product_addons"] = 0
        for link in ADDON_LINKS:
            addon = addons[link["addon"]]
            for category_slug in link["categories"]:
                for product in Product.objects.filter(
                    category=categories[category_slug]
                ):
                    _, was_created = ProductAddOn.objects.get_or_create(
                        product=product,
                        addon=addon,
                        defaults={
                            "min_quantity": link["min_quantity"],
                            "max_quantity": link["max_quantity"],
                        },
                    )
                    created["product_addons"] += int(was_created)

        created["promo_codes"] = 0
        for row in PROMO_ROWS:
            data = dict(row)
            code = data.pop("code")
            _, was_created = PromoCode.objects.get_or_create(
                code=code,
                defaults={**data, "is_active": True},
            )
            created["promo_codes"] += int(was_created)

        admin_password = config(
            "STAGING_ADMIN_PASSWORD", default="Admin1234!"
        )
        admin, was_created = Customer.objects.get_or_create(
            phone=ADMIN_PHONE,
            defaults={
                "full_name": "مدیر رستوران",
                "is_staff": True,
                "is_superuser": True,
                "is_active": True,
            },
        )
        changed = was_created
        if not admin.is_staff:
            admin.is_staff = True
            changed = True
        if not admin.is_superuser:
            admin.is_superuser = True
            changed = True
        if not admin.is_active:
            admin.is_active = True
            changed = True
        # Keep a manually changed password, but make sure an account that was
        # created through OTP (unusable password) can actually log in.
        if was_created or not admin.password or not admin.has_usable_password():
            admin.set_password(admin_password)
            changed = True
        if changed:
            admin.save()
        created["admin"] = int(was_created)

        customer, was_created = Customer.objects.get_or_create(
            phone=SAMPLE_CUSTOMER_PHONE,
            defaults={"full_name": "مشتری نمونه"},
        )
        created["customer"] = int(was_created)

        created["addresses"] = 0
        has_default = CustomerAddress.objects.filter(
            customer=customer, is_default=True
        ).exists()
        for index, row in enumerate(ADDRESS_ROWS):
            _, was_created = CustomerAddress.objects.get_or_create(
                customer=customer,
                title=row["title"],
                defaults={
                    "address_text": row["address_text"],
                    "recipient_name": row["recipient_name"],
                    "recipient_phone": row["recipient_phone"],
                    "is_out_of_zone": row["is_out_of_zone"],
                    "is_default": not has_default and index == 0,
                },
            )
            created["addresses"] += int(was_created)

        # Catalog/CMS selectors cache reads; make new seed data visible after
        # the transaction commits rather than serving a warm pre-seed menu.
        transaction.on_commit(cache.clear)

        summary = ", ".join(
            f"{name}+{count}" for name, count in created.items() if count
        )
        if not summary:
            summary = "nothing new (already seeded)"
        self.stdout.write(self.style.SUCCESS(f"Staging seed complete: {summary}."))
