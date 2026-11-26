from __future__ import annotations

from typing import Any

from django.db import models

from common.models import BaseModel


def normalize_promo_code(value: str) -> str:
    """Promo codes are case-insensitive and stored in a canonical form."""
    return (value or "").strip().upper()


class Order(BaseModel):
    class Status(models.TextChoices):
        PENDING_PAYMENT = "PENDING_PAYMENT", "Pending payment"
        PROCESSING = "PROCESSING", "Processing"
        READY = "READY", "Ready"
        COMPLETED = "COMPLETED", "Completed"
        CANCELED = "CANCELED", "Canceled"

    class PaymentStatus(models.TextChoices):
        UNPAID = "UNPAID", "Unpaid"
        PAID = "PAID", "Paid"
        AWAITING_REFUND = "AWAITING_REFUND", "Awaiting refund"
        REFUNDED = "REFUNDED", "Refunded"

    class DeliveryType(models.TextChoices):
        PICKUP = "PICKUP", "Pickup"
        DELIVERY = "DELIVERY", "Delivery"

    customer = models.ForeignKey(
        "accounts.Customer",
        on_delete=models.PROTECT,
        related_name="orders",
    )

    status = models.CharField(
        max_length=32,
        choices=Status.choices,
        default=Status.PENDING_PAYMENT,
        db_index=True,
    )
    payment_status = models.CharField(
        max_length=32,
        choices=PaymentStatus.choices,
        default=PaymentStatus.UNPAID,
        db_index=True,
    )

    delivery_type = models.CharField(max_length=16, choices=DeliveryType.choices)
    delivery_address = models.ForeignKey(
        "accounts.CustomerAddress",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="orders",
    )
    delivery_address_snapshot = models.TextField(blank=True)
    delivery_recipient_name = models.CharField(max_length=128, blank=True)
    delivery_recipient_phone = models.CharField(max_length=15, blank=True)

    subtotal = models.PositiveIntegerField(default=0)
    delivery_fee = models.PositiveIntegerField(default=0)
    packaging_fee = models.PositiveIntegerField(default=0)
    promo_code_snapshot = models.CharField(max_length=50, blank=True)
    discount_amount = models.PositiveIntegerField(default=0)
    total_amount = models.PositiveIntegerField(default=0)

    prep_time_minutes = models.PositiveSmallIntegerField(default=0)
    expected_ready_at = models.DateTimeField(null=True, blank=True, db_index=True)
    paid_at = models.DateTimeField(null=True, blank=True)

    notes_to_kitchen = models.TextField(blank=True)

    is_printed = models.BooleanField(default=False, db_index=True)
    printed_at = models.DateTimeField(null=True, blank=True)

    daily_number = models.PositiveIntegerField(null=True, blank=True, db_index=True)
    daily_number_date = models.DateField(null=True, blank=True, db_index=True)

    expires_at = models.DateTimeField(null=True, blank=True, db_index=True)

    canceled_at = models.DateTimeField(null=True, blank=True)
    cancellation_reason = models.TextField(blank=True)
    cancellation_requested = models.BooleanField(default=False, db_index=True)
    cancellation_request_reason = models.TextField(blank=True)
    cancellation_requested_at = models.DateTimeField(null=True, blank=True)
    canceled_by = models.ForeignKey(
        "accounts.Customer",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="canceled_orders",
    )

    refund_card_number = models.CharField(max_length=32, blank=True)
    refund_tracking_code = models.CharField(max_length=64, blank=True)
    refunded_at = models.DateTimeField(null=True, blank=True)
    refunded_by = models.ForeignKey(
        "accounts.Customer",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="refunded_orders",
    )

    class Meta(BaseModel.Meta):
        ordering = ("-created_at",)
        constraints = [
            models.UniqueConstraint(
                fields=["daily_number_date", "daily_number"],
                condition=models.Q(daily_number__isnull=False),
                name="unique_order_daily_number_per_date",
            ),
        ]
        verbose_name = "Order"
        verbose_name_plural = "Orders"

    def __str__(self) -> str:
        label = self.daily_number or self.pk
        return f"Order #{label} ({self.status})"


class PromoCode(BaseModel):
    class DiscountType(models.TextChoices):
        PERCENTAGE = "PERCENTAGE", "Percentage"
        FIXED = "FIXED", "Fixed amount"

    code = models.CharField(max_length=50, unique=True, db_index=True)
    discount_type = models.CharField(
        max_length=16,
        choices=DiscountType.choices,
        default=DiscountType.PERCENTAGE,
    )
    discount_value = models.PositiveIntegerField()
    max_discount_amount = models.PositiveIntegerField(null=True, blank=True)
    min_order_amount = models.PositiveIntegerField(default=0)
    valid_from = models.DateTimeField(null=True, blank=True)
    valid_until = models.DateTimeField(null=True, blank=True)
    max_total_uses = models.PositiveIntegerField(null=True, blank=True)
    max_uses_per_customer = models.PositiveIntegerField(default=1)
    first_order_only = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta(BaseModel.Meta):
        verbose_name = "Promo Code"
        verbose_name_plural = "Promo Codes"

    def __str__(self) -> str:
        return self.code

    def save(self, *args: Any, **kwargs: Any) -> None:
        self.code = normalize_promo_code(self.code)
        super().save(*args, **kwargs)


class PromoCodeUsage(BaseModel):
    promo_code = models.ForeignKey(
        PromoCode,
        on_delete=models.PROTECT,
        related_name="usages",
    )
    customer = models.ForeignKey(
        "accounts.Customer",
        on_delete=models.CASCADE,
        related_name="promo_usages",
    )
    order = models.OneToOneField(
        "orders.Order",
        on_delete=models.CASCADE,
        related_name="promo_usage",
    )
    discount_amount = models.PositiveIntegerField()

    class Meta(BaseModel.Meta):
        verbose_name = "Promo Code Usage"
        verbose_name_plural = "Promo Code Usages"

    def __str__(self) -> str:
        return f"{self.promo_code_id} -> order {self.order_id}"


class OrderItem(BaseModel):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(
        "catalog.Product",
        on_delete=models.PROTECT,
        related_name="order_items",
    )
    product_name_snapshot = models.CharField(max_length=255)
    unit_price_snapshot = models.PositiveIntegerField()
    quantity = models.PositiveSmallIntegerField()
    addons_total = models.PositiveIntegerField(default=0)
    line_total = models.PositiveIntegerField()

    class Meta(BaseModel.Meta):
        ordering = ("id",)
        verbose_name = "Order Item"
        verbose_name_plural = "Order Items"

    def __str__(self) -> str:
        return f"{self.product_name_snapshot} x{self.quantity}"


class OrderItemAddOn(BaseModel):
    order_item = models.ForeignKey(
        OrderItem, on_delete=models.CASCADE, related_name="addons"
    )
    addon = models.ForeignKey(
        "catalog.AddOn",
        on_delete=models.PROTECT,
        related_name="order_item_addons",
    )
    addon_name_snapshot = models.CharField(max_length=128)
    unit_price_snapshot = models.PositiveIntegerField()
    quantity = models.PositiveSmallIntegerField()
    line_total = models.PositiveIntegerField()

    class Meta(BaseModel.Meta):
        ordering = ("id",)
        verbose_name = "Order Item Add-on"
        verbose_name_plural = "Order Item Add-ons"

    def __str__(self) -> str:
        return f"{self.addon_name_snapshot} x{self.quantity}"