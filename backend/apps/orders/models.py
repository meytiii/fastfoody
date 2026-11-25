from __future__ import annotations

from django.db import models

from common.models import BaseModel


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