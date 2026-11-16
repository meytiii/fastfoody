from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from common.models import BaseModel
from common.utils import normalize_phone_number


class UserManager(BaseUserManager):
    def create_user(self, phone_number: str, full_name: str = "", password: str = None, **extra_fields):
        if not phone_number:
            raise ValueError("شماره موبایل الزامی است.")
        phone_number = normalize_phone_number(phone_number)
        user = self.model(phone_number=phone_number, full_name=full_name, **extra_fields)
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        user.save(using=self._db)
        return user

    def create_superuser(self, phone_number: str, full_name: str = "Admin", password: str = None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        return self.create_user(phone_number, full_name, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin, BaseModel):
    phone_number = models.CharField(max_length=11, unique=True, db_index=True)
    full_name = models.CharField(max_length=150, blank=True)
    is_active = models.BooleanField(default=True)
    is_blocked = models.BooleanField(default=False, help_text="مسدود شده توسط مدیر در CRM")
    is_staff = models.BooleanField(default=False, help_text="دسترسی به پنل مدیریت/صندوق")

    objects = UserManager()

    USERNAME_FIELD = "phone_number"
    REQUIRED_FIELDS = ["full_name"]

    class Meta:
        db_table = "accounts_user"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.full_name or 'کاربر'} ({self.phone_number})"


class CustomerAddress(BaseModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="addresses")
    title = models.CharField(max_length=100, help_text="مثلاً: خانه، محل کار")
    full_address = models.TextField()
    postal_code = models.CharField(max_length=20, blank=True)
    is_out_of_zone = models.BooleanField(
        default=False,
        help_text="اگر True باشد، تعرفه پیک خارج از شهر محاسبه می‌شود.",
    )
    is_default = models.BooleanField(default=False)

    class Meta:
        db_table = "accounts_customer_address"
        ordering = ["-is_default", "-created_at"]

    def __str__(self):
        return f"{self.title} - {self.user.phone_number}"


class CustomerNote(BaseModel):
    """یادداشت‌های داخلی مدیر در پرونده CRM مشتری (روی فیش صندوق هم می‌تواند نمایش داده شود)"""
    customer = models.ForeignKey(User, on_delete=models.CASCADE, related_name="crm_notes")
    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="authored_notes")
    note = models.TextField()
    show_on_pos_receipt = models.BooleanField(
        default=True,
        help_text="آیا این یادداشت هنگام ثبت سفارش جدید روی مانیتور صندوق نمایش داده شود؟",
    )

    class Meta:
        db_table = "accounts_customer_note"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Note on {self.customer.phone_number}"