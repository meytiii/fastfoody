import secrets
from django.db import models
from common.models import BaseModel
from apps.accounts.models import User
from apps.catalog.models import Product, AddOn


def generate_tracking_code() -> str:
    return str(secrets.randbelow(899999) + 100000)


class Order(BaseModel):
    class Status(models.TextChoices):
        PENDING_PAYMENT = "pending_payment", "در انتظار پرداخت"
        PROCESSING = "processing", "در حال آماده‌سازی"
        READY = "ready", "آماده تحویل / ارسال شده"
        COMPLETED = "completed", "تکمیل شده"
        CANCELED = "canceled", "لغو شده"

    class PaymentStatus(models.TextChoices):
        UNPAID = "unpaid", "پرداخت نشده"
        PAID = "paid", "پرداخت موفق"
        AWAITING_REFUND = "awaiting_refund", "در انتظار عودت وجه (کارت‌به‌کارت)"
        REFUNDED = "refunded", "مبلغ عودت داده شد"

    class DeliveryType(models.TextChoices):
        PICKUP = "pickup", "تحویل حضوری در رستوران"
        DELIVERY = "delivery", "ارسال با پیک"

    user = models.ForeignKey(User, on_delete=models.PROTECT, related_name="orders")
    
    # شماره روزانه فیش فقط پس از پرداخت موفق (Verify زرین‌پال) تخصیص داده می‌شود
    daily_number = models.PositiveIntegerField(null=True, blank=True, db_index=True)
    tracking_code = models.CharField(max_length=12, default=generate_tracking_code, unique=True, db_index=True)

    status = models.CharField(
        max_length=25,
        choices=Status.choices,
        default=Status.PENDING_PAYMENT,
        db_index=True,
    )
    payment_status = models.CharField(
        max_length=25,
        choices=PaymentStatus.choices,
        default=PaymentStatus.UNPAID,
        db_index=True,
    )
    delivery_type = models.CharField(max_length=15, choices=DeliveryType.choices)

    # اسنپ‌شات اطلاعات مشتری و آدرس در لحظه ثبت سفارش
    customer_name_snapshot = models.CharField(max_length=150)
    customer_phone_snapshot = models.CharField(max_length=15)
    address_snapshot = models.TextField(blank=True, help_text="در صورت تحویل حضوری خالی است")
    is_out_of_zone = models.BooleanField(default=False)
    customer_note = models.TextField(blank=True, help_text="توضیحات مشتری روی سفارش (مثلاً: زنگ واحد خراب است)")

    # مبالغ مالی (تومان)
    items_total_amount = models.PositiveIntegerField(default=0)
    delivery_cost = models.PositiveIntegerField(default=0)
    payable_amount = models.PositiveIntegerField(default=0)

    # مدیریت زمان آماده‌سازی
    estimated_prep_minutes = models.PositiveSmallIntegerField(
        default=25,
        help_text="Max(items prep time) + buffer (قابل ویرایش توسط مدیر)",
    )
    paid_at = models.DateTimeField(null=True, blank=True, db_index=True)
    expected_ready_at = models.DateTimeField(null=True, blank=True)
    ready_at = models.DateTimeField(null=True, blank=True)

    # وضعیت چاپ فیش در مانیتور صندوق
    is_printed = models.BooleanField(default=False, db_index=True)

    # مدیریت لغو و عودت وجه دستی (Refund)
    cancel_requested_by_user = models.BooleanField(default=False)
    cancel_reason = models.TextField(blank=True)
    refund_card_number = models.CharField(max_length=20, blank=True, help_text="شماره کارت ۱۶ رقمی مشتری جهت عودت وجه")
    refund_tracking_ref = models.CharField(max_length=100, blank=True, help_text="شماره پیگیری کارت‌به‌کارت مدیر")
    refunded_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "orders_order"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status", "payment_status", "-paid_at"]),
        ]

    def __str__(self):
        return f"Order #{self.daily_number or self.tracking_code} - {self.get_status_display()}"


class OrderItem(BaseModel):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, related_name="order_items")
    
    # اسنپ‌شات محصول در لحظه خرید
    product_name_snapshot = models.CharField(max_length=200)
    unit_price_snapshot = models.PositiveIntegerField(help_text="قیمت واحد غذا در لحظه خرید")
    prep_time_snapshot = models.PositiveSmallIntegerField(default=20)
    
    quantity = models.PositiveSmallIntegerField(default=1)
    line_total_amount = models.PositiveIntegerField(
        help_text="(قیمت واحد غذا + جمع افزودنی‌های این ردیف) * تعداد این ردیف"
    )

    class Meta:
        db_table = "orders_order_item"

    def __str__(self):
        return f"{self.quantity}x {self.product_name_snapshot}"


class OrderItemAddOn(BaseModel):
    order_item = models.ForeignKey(OrderItem, on_delete=models.CASCADE, related_name="selected_addons")
    addon = models.ForeignKey(AddOn, on_delete=models.SET_NULL, null=True)
    
    # اسنپ‌شات افزودنی در لحظه خرید
    addon_name_snapshot = models.CharField(max_length=120)
    unit_price_snapshot = models.PositiveIntegerField()
    quantity = models.PositiveSmallIntegerField(default=1, help_text="تعداد این افزودنی به ازای هر ۱ عدد از غذای مربوطه")

    class Meta:
        db_table = "orders_order_item_addon"

    def __str__(self):
        return f"+ {self.quantity}x {self.addon_name_snapshot}"