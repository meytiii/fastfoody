from __future__ import annotations

from django.db import models

from common.models import BaseModel


class Payment(BaseModel):
    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        SUCCEEDED = "SUCCEEDED", "Succeeded"
        FAILED = "FAILED", "Failed"
        CANCELED = "CANCELED", "Canceled"

    order = models.ForeignKey(
        "orders.Order",
        on_delete=models.PROTECT,
        related_name="payments",
    )
    amount = models.PositiveIntegerField()
    status = models.CharField(
        max_length=16,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True,
    )

    authority = models.CharField(max_length=128, db_index=True)
    ref_id = models.CharField(max_length=64, blank=True, db_index=True)

    gateway_response_code = models.IntegerField(null=True, blank=True)
    gateway_response_message = models.TextField(blank=True)

    verified_at = models.DateTimeField(null=True, blank=True)
    failed_at = models.DateTimeField(null=True, blank=True)
    canceled_at = models.DateTimeField(null=True, blank=True)

    class Meta(BaseModel.Meta):
        ordering = ("-created_at",)
        constraints = [
            models.UniqueConstraint(
                fields=["authority"],
                condition=models.Q(deleted_at__isnull=True),
                name="unique_alive_payment_authority",
            ),
        ]
        verbose_name = "Payment"
        verbose_name_plural = "Payments"

    def __str__(self) -> str:
        return f"Payment {self.pk} for order {self.order_id} ({self.status})"