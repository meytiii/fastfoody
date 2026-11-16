from __future__ import annotations

from typing import Any

from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.contrib.auth.models import PermissionsMixin
from django.core.exceptions import ValidationError
from django.db import models

from common.models import BaseModel


class CustomerManager(BaseUserManager):
    use_in_migrations = True

    def create_user(
        self,
        phone: str,
        password: str | None = None,
        **extra_fields: Any,
    ) -> "Customer":
        if not phone:
            raise ValueError("Phone number is required")

        phone = str(phone).strip()
        user = self.model(phone=phone, **extra_fields)

        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()

        user.save(using=self._db)
        return user

    def create_superuser(
        self,
        phone: str,
        password: str,
        **extra_fields: Any,
    ) -> "Customer":
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self.create_user(phone=phone, password=password, **extra_fields)


class Customer(AbstractBaseUser, PermissionsMixin):
    phone = models.CharField(max_length=15, unique=True, db_index=True)
    full_name = models.CharField(max_length=255, blank=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_blocked = models.BooleanField(default=False)
    date_joined = models.DateTimeField(auto_now_add=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = CustomerManager()

    USERNAME_FIELD = "phone"
    REQUIRED_FIELDS: list[str] = []

    class Meta:
        ordering = ("-created_at",)
        verbose_name = "Customer"
        verbose_name_plural = "Customers"

    def __str__(self) -> str:
        return self.phone


class CustomerAddress(BaseModel):
    customer = models.ForeignKey(
        Customer,
        on_delete=models.CASCADE,
        related_name="addresses",
    )
    title = models.CharField(max_length=64, blank=True)
    address_text = models.TextField()
    recipient_name = models.CharField(max_length=128, blank=True)
    recipient_phone = models.CharField(max_length=15, blank=True)
    is_out_of_zone = models.BooleanField(default=False)
    is_default = models.BooleanField(default=False)

    class Meta(BaseModel.Meta):
        ordering = ("-is_default", "-created_at")
        constraints = [
            models.UniqueConstraint(
                fields=["customer"],
                condition=models.Q(is_default=True, deleted_at__isnull=True),
                name="unique_default_address_per_customer",
            ),
        ]
        verbose_name = "Customer Address"
        verbose_name_plural = "Customer Addresses"

    def __str__(self) -> str:
        return f"{self.customer.phone}: {self.address_text[:40]}"


class CustomerNote(BaseModel):
    customer = models.ForeignKey(
        Customer,
        on_delete=models.CASCADE,
        related_name="notes",
    )
    author = models.ForeignKey(
        Customer,
        on_delete=models.SET_NULL,
        related_name="authored_notes",
        null=True,
        blank=True,
    )
    text = models.TextField()

    class Meta(BaseModel.Meta):
        ordering = ("-created_at",)
        verbose_name = "Customer Note"
        verbose_name_plural = "Customer Notes"

    def __str__(self) -> str:
        return f"Note for {self.customer.phone} ({self.created_at:%Y-%m-%d})"