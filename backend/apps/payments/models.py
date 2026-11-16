from django.db import models
from common.models import BaseModel
from apps.orders.models import Order


class Transaction(BaseModel):
    class Status(models.TextChoices):
        INITIATED = "initiated", "ارسال شده به درگاه"
        SUCCESS = "success", "تایید شده (Verified)"
        FAILED = "failed", "ناموفق / لغو توسط کاربر"

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="transactions")
    amount = models.PositiveIntegerField(help_text="مبلغ به تومان")
    authority = models.CharField(max_length=64, unique=True, db_index=True)
    ref_id = models.CharField(max_length=64, blank=True, db_index=True)
    card_pan = models.CharField(max_length=32, blank=True, help_text="شماره کارت ماسک شده پرداخت‌کننده")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.INITIATED, db_index=True)
    gateway_response = models.JSONField(default=dict, blank=True)
    verified_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "payments_transaction"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Tx {self.authority} - {self.get_status_display()}"