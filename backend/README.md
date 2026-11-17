## مستند جامع پروژه — FastFood Backend

این سند یک راهنمای کامل از صفر تا صد است: چرا هر ماژول وجود دارد، چطور کار می‌کند، و در انتها یک چک‌لیست کامل برای تأیید عملکرد بک‌اند.

نحوه استفاده: اگر تازه با پروژه آشنا می‌شوید، از بخش ۱ به ترتیب بخوانید. اگر می‌خواهید سریع تست کنید، به بخش ۱۰ (چک‌لیست نهایی) بروید. اگر باگ دیدید، بخش ۹ (Troubleshooting) پاسخ اکثر مشکلات را دارد.

نسخه‌بندی: این سند وضعیت پس از Phase 9 (JWT + Backoffice Session) را توصیف می‌کند.

## فهرست مطالب

- نمای کلی پروژه
- ساختار پوشه‌ها
- پشته فناوری و تصمیمات کلیدی
- راه‌اندازی سریع (Local)
- پیکربندی و متغیرهای محیطی
- معماری جریان درخواست
- ماژول‌ها به تفصیل
- 7.1 Common
- 7.2 Accounts
- 7.3 CMS
- 7.4 Catalog
- 7.5 Orders
- 7.6 Payments
- احراز هویت و مجوزها
- مرجع کامل API
- عیب‌یابی
- چک‌لیست نهایی (تست کامل بک‌اند)

## 1. نمای کلی پروژه

بک‌اند یک رستوران فست‌فود تک‌شعبه است که دو ناحیه API کاملاً جدا دارد:

| ناحیه | مسیر | کاربر | احراز هویت |
| --- | --- | --- | --- |
| Storefront | /api/v1/storefront/ | مشتری | OTP + JWT (و session به‌عنوان fallback) |
| Backoffice | /api/v1/backoffice/ | کارمند/مدیر | Password + Session |

Django admin غیرفعال است. همه‌ی عملیات مدیریتی از طریق Backoffice API انجام می‌شود (تصمیم D5).

### قابلیت‌ها

- منوی آنلاین با دسته‌بندی، محصول، افزودنی دو لایه
- گردونه شانس (Lucky Wheel) روی محصولات main dish
- OTP با محدودیت نرخ برای ورود مشتری
- سبد خرید سمت فرانت (localStorage)، ثبت سفارش در سرور
- پرداخت آنلاین از طریق زرین‌پال v4 با idempotency کامل
- ردیابی زنده سفارش (polling هر ۱۰–۱۵ ثانیه)
- Live POS برای آشپزخانه با چاپ رسید و آلارم
- CRM (پروفایل ۳۶۰ درجه + یادداشت داخلی + LTV)
- CMS (تنظیمات رستوران + محتوای بخش‌ها + رسانه با WebP)
- روند بازپرداخت دستی توسط مدیر (paid → awaiting_refund → refunded)

## 2. ساختار پوشه‌ها

```text
fastfood-backend/
├── config/
│   ├── __init__.py            # celery_app را export می‌کند
│   ├── settings.py            # تنها فایل settings (D1 — بدون split)
│   ├── settings_sqlite.py     # فقط برای dev local
│   ├── celery.py              # app + autodiscover
│   ├── urls.py                # health + schema + docs + mounts
│   ├── api_urls_storefront.py
│   ├── api_urls_backoffice.py
│   ├── wsgi.py / asgi.py
│   └── gunicorn.conf.py       # production config
│
├── common/                    # هسته مشترک
│   ├── models.py              # BaseModel, SoftDelete*
│   ├── exceptions.py          # BusinessException + 6 زیرکلاس
│   ├── exception_handler.py   # envelope پاسخ خطا
│   ├── permissions.py         # IsStaffUser
│   ├── views.py               # BackofficeAPIView
│   ├── cache.py               # make_cache_key
│   ├── redis_client.py        # کلاینت مشترک Redis
│   ├── sms.py                 # sms.ir wrapper
│   ├── images.py              # WebP conversion
│   └── checks.py              # production safety checks
│
├── apps/
│   ├── accounts/
│   │   ├── models.py          # Customer, CustomerAddress, CustomerNote
│   │   ├── otp.py             # Redis-only OTP
│   │   ├── tokens.py          # JWT issue/blacklist
│   │   ├── selectors.py
│   │   ├── services.py
│   │   ├── tasks.py           # send_otp_sms
│   │   ├── throttles.py
│   │   ├── exceptions.py
│   │   ├── management/commands/create_staff.py
│   │   └── apis/{storefront,backoffice}/
│   │
│   ├── cms/                   # RestaurantSettings, SiteSection, MediaAsset
│   ├── catalog/               # Category, Product, AddOn, ProductAddOn
│   ├── orders/                # Order, OrderItem, OrderItemAddOn
│   └── payments/              # Payment + ZarinpalClient
│
├── tests/                     # pytest suite
├── docs/                      # مستندات این پروژه
├── requirements.txt
├── pytest.ini
├── manage.py
└── .env.example
```

### قواعد ساختاری

هر app سه لایه دارد: models.py / selectors.py (خواندن) / services.py (نوشتن).

API layer در apis/storefront/ و apis/backoffice/ جدا است — هیچ business logic در view یا serializer نیست.

هیچ Repository layer وجود ندارد (D19).

## 3. پشته فناوری و تصمیمات کلیدی

| لایه | فناوری |
| --- | --- |
| Framework | Django 5.x + DRF 3.15 |
| DB | PostgreSQL 16 (dev: SQLite) |
| Cache | Redis 7 |
| Async | Celery 5.4 + Beat (۲ صف: high_priority و default) |
| JWT | djangorestframework-simplejwt (فقط Storefront) |
| Images | Pillow → WebP |
| Docs | drf-spectacular (Swagger جدا برای هر ناحیه) |
| Tests | pytest + pytest-django + Factory Boy |

تصمیمات قفل‌شده (از D1–D25 + JWT)

| # | تصمیم | پیامد در کد |
| --- | --- | --- |
| D1 | پول = integer تومان | هیچ Decimal ای نیست |
| D2 | Timezone = Asia/Tehran، USE_TZ=True | daily_number_date بر اساس timezone.localdate() |
| D3 | Custom user = accounts.Customer | AUTH_USER_MODEL = "accounts.Customer" |
| D4 | Backoffice = Session + is_staff | BackofficeAPIView فقط SessionAuthentication |
| D5 | Django admin غیرفعال | django.contrib.admin در INSTALLED_APPS نیست |
| D6 | Soft delete در BaseModel | objects فقط alive را می‌بیند |
| D7 | daily_number = Redis INCR | _assign_daily_number |
| D8 | OTP فقط در Redis، TTL 120s | apps/accounts/otp.py |
| D9 | Throttle: otp_request 5/h، otp_verify 10/h | common/views.py نیست — throttle class در throttles.py |
| D10 | هزینه ارسال بر اساس is_out_of_zone | _resolve_address + settings |
| D11 | مشتری نمی‌تواند سفارش پرداخت‌شده را لغو کند | فقط manager cancel |
| D12 | prep = max(items) + buffer | _compute_prep_time |
| D13 | Live POS polling + is_printed | get_live_orders + mark_order_printed |
| D14 | Zarinpal/sms.ir از env | settings.ZARINPAL_*, SMS_IR_* |
| D15 | دو صف Celery | CELERY_TASK_ROUTES |
| D16 | Error envelope | common/exception_handler.py |
| D17 | BaseModel fields | created_at, updated_at, deleted_at |
| D18 | ۶ زیرکلاس BusinessException | common/exceptions.py |
| D19 | بدون Repository layer | selectors + services فقط |
| D20 | بدون Variant model | محصولات سایز مختلف = رکورد جدا |
| D21 | Product status enum + is_main_dish | Product.Status, is_main_dish boolean |
| D22 | AddOn دو لایه | AddOn global + ProductAddOn per-product |
| D23 | SiteSection JSON | ۶ کلید مجاز |
| D24 | RestaurantSettings singleton | save() اجباری pk=1 |
| D25 | WebP conversion | common/images.py (اول Product.image، MediaAsset.file) |

JWT: Storefront JWT + Session → Backoffice Session فقط

## 4. راه‌اندازی سریع (Local)

### پیش‌نیاز

- Python 3.12
- Redis 7 (با Docker یا نصب مستقیم)

```powershell
# Redis با Docker
docker run -d --name fastfood-redis -p 6379:6379 redis:7-alpine

# یا اگر نصب مستقیم دارید
redis-server
```

### نصب

```powershell
cd backend
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
```

.env برای dev (SQLite)

```dotenv
SECRET_KEY=dev-key-not-for-production
DEBUG=True
ALLOWED_HOSTS=127.0.0.1,localhost

# SQLite — نیازی به Postgres نیست
# مسیر database در settings_sqlite.py تعریف شده

REDIS_URL=redis://127.0.0.1:6379/0
CELERY_BROKER_URL=redis://127.0.0.1:6379/1
CELERY_RESULT_BACKEND=redis://127.0.0.1:6379/2

MANAGER_PHONE=09123456789

ZARINPAL_MERCHANT_ID=
ZARINPAL_SANDBOX=True
ZARINPAL_CALLBACK_URL=http://127.0.0.1:8000/api/v1/storefront/payments/callback/
PAYMENT_FRONTEND_RESULT_URL=http://localhost:3000/payment/result

SMS_IR_API_KEY=
SMS_IR_SENDER=

JWT_ACCESS_LIFETIME_MINUTES=60
JWT_REFRESH_LIFETIME_DAYS=7
```

`config/settings_sqlite.py`

```python
from __future__ import annotations

from .settings import *  # noqa: F401,F403

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",  # noqa: F405
    }
}

CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True
```

توضیح: CELERY_TASK_ALWAYS_EAGER = True باعث می‌شود همه‌ی taskهای Celery (OTP SMS، سفارش، تغییر prep time) به‌جای صف Redis، inline در پروسه‌ی runserver اجرا شوند. برای dev ایده‌آل است چون نه worker لازم است نه beat.

### راه‌اندازی

```powershell
python manage.py migrate --settings=config.settings_sqlite
python manage.py create_staff 09123456789 "Test@1234" --superuser --settings=config.settings_sqlite
python manage.py runserver --settings=config.settings_sqlite
```

سرور روی http://127.0.0.1:8000 بالا می‌آید. بررسی:

```bash
curl http://127.0.0.1:8000/health/
# {"success": true, "data": {"status": "ok"}}
```

نکته: اگر --settings را زیاد تایپ می‌کنید، یک alias در PowerShell بسازید:

```powershell
function devpy { python manage.py @args --settings=config.settings_sqlite }
devpy migrate
devpy create_staff 09123456789 "Test@1234" --superuser
devpy runserver
```

## 5. پیکربندی و متغیرهای محیطی

| متغیر | الزام؟ | پیش‌فرض | توضیح |
| --- | --- | --- | --- |
| SECRET_KEY | ✅ در prod | dev-insecure | کلید امضای session، CSRF، JWT |
| DEBUG | — | False | در dev True |
| ALLOWED_HOSTS | ✅ در prod | 127.0.0.1,localhost | comma-separated |
| REDIS_URL | ✅ | redis://127.0.0.1:6379/0 | Cache backend |
| CELERY_BROKER_URL | ✅ | redis://.../1 | صف taskها |
| CELERY_RESULT_BACKEND | — | redis://.../2 | نتیجه‌ی taskها |
| MANAGER_PHONE | توصیه | خالی | برای SMS سفارش جدید |
| ZARINPAL_MERCHANT_ID | ✅ در prod | خالی | — |
| ZARINPAL_CALLBACK_URL | ✅ در dev | باید HTTPS باشد در prod | — |
| ZARINPAL_SANDBOX | — | True | در prod False |
| SMS_IR_API_KEY | توصیه | خالی | اگر خالی، SMS لاگ می‌شود |
| SMS_IR_SENDER | توصیه | خالی | شماره خط |
| PAYMENT_FRONTEND_RESULT_URL | توصیه | dev URL | کاربر بعد از پرداخت به آنجا redirect می‌شود |
| JWT_ACCESS_LIFETIME_MINUTES | — | 60 | — |
| JWT_REFRESH_LIFETIME_DAYS | — | 7 | — |

در dev: اگر SMS_IR_API_KEY خالی باشد، پیام‌ها در کنسول runserver لاگ می‌شوند. یعنی OTP را از کنسول می‌خوانید — نیازی به SMS واقعی نیست.

## 6. معماری جریان درخواست

### الگوی کلی

```text
[Client] → [Django URL] → [APIView] → [Serializer.validate]
                                       ↓
                          ┌────────────┴────────────┐
                          ↓                         ↓
                       [Selector]              [Service]
                       (read)                  (write)
                          ↓                         ↓
                       [ORM]                    [ORM + @transaction.atomic]
                                                     ↓
                                            [on_commit → cache.delete / Celery task]
                          ↓
                     [Response] → [Client]
```

### قواعد طلایی

Views و Serializers فقط validation و serialization. هیچ منطق کسب‌وکاری.

همه‌ی خواندن‌ها در selectors.py. هیچ‌جا Model.objects.filter(...) در view نیست.

همه‌ی نوشتن‌ها در services.py. هیچ Model instance در view ساخته/ذخیره نمی‌شود.

@transaction.atomic روی هر service که بیش از یک جدول را تغییر می‌دهد یا state transition دارد.

transaction.on_commit() برای side-effectهای بیرونی (Celery task، cache invalidation).

### پوشش خطا (D16)

هر پاسخ غیر 2xx:

```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE_STRING",
    "message": "پیام فارسی برای کاربر",
    "details": null
  }
}
```

details می‌تواند null، یک dict از field→message، یا هر ساختار کمکی باشد.

پاسخ‌های موفق data را مستقیم برمی‌گردانند (بدون wrapper).

## 7. ماژول‌ها به تفصیل

### 7.1 هستهٔ مشترک

#### BaseModel + Soft Delete (D17)

```python
class BaseModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True, db_index=True)

    objects = SoftDeleteManager()   # فقط alive
    all_objects = models.Manager()  # همه

    def soft_delete(self): ...      # deleted_at = now()
    def restore(self): ...          # deleted_at = None
    def hard_delete(self): ...      # حذف فیزیکی
    def delete(self, ...): ...      # soft_delete() را صدا می‌زند
```

چرا: حذف هیچ‌وقت فیزیکی نیست تا audit trail حفظ شود. objects هرگز رکورد حذف‌شده را برنمی‌گرداند.

SoftDeleteQuerySet:

- .alive() — فقط deleted_at IS NULL
- .dead() — فقط deleted_at NOT NULL
- .delete() — به‌جای حذف، UPDATE deleted_at=now()
- .hard_delete() — حذف واقعی

#### استثناها (D18)

```text
BusinessException (status 400)
├── NotFoundError            (404, NOT_FOUND)
├── PermissionDeniedError    (403, PERMISSION_DENIED)
├── ValidationError          (422, VALIDATION_ERROR)
├── RestaurantClosedError    (409, RESTAURANT_CLOSED)
├── OrderStateError          (409, INVALID_ORDER_STATE)
└── PaymentError             (402, PAYMENT_ERROR)
```

هر subclass در appهای مختلف ممکن است default_code را override کند:

```python
class OTPExpiredError(ValidationError):
    default_code = "OTP_EXPIRED"
    status_code = 400
```

`custom_exception_handler`

```python
def custom_exception_handler(exc, context):
    if isinstance(exc, BusinessException):
        # از code/message/status خودش استفاده می‌کند
    if isinstance(exc, DjangoValidationError):
        # → 422 با envelope
    response = drf_exception_handler(exc, context)
    if response:
        # DRF exception → wrap در envelope
    # پیش‌فرض: 500 با پیام ژنریک (بدون leak)
```

#### BackofficeAPIView

```python
class BackofficeAPIView(APIView):
    authentication_classes = [SessionAuthentication]  # نه JWT
    permission_classes = [IsStaffUser]
```

چرا جدا: تضمین می‌کند JWT (که فقط برای Storefront است) روی Backoffice پذیرفته نشود. اگر مهاجم توکن مشتری را داشته باشد، نمی‌تواند به backoffice حمله کند — مگر اینکه staff هم باشد و session داشته باشد.

#### common/cache.py

```python
CACHE_VERSION = "v1"
def make_cache_key(area: str, scope: str, version: str = CACHE_VERSION) -> str:
    return f"{area}:{scope}:{version}"
```

Cache backend از KEY_PREFIX="fastfood" استفاده می‌کند، پس کلید نهایی می‌شود:

```text
fastfood:catalog:storefront_menu:v1
```

#### common/sms.py

```python
def send_sms(*, phone: str, message: str) -> bool
```

اگر SMS_IR_API_KEY خالی است → فقط لاگ می‌کند و True برمی‌گرداند (برای dev).

در غیر این صورت → POST https://api.sms.ir/v1/send/bulk با x-api-key.

روی هر خطا False برمی‌گرداند (بدون exception).

#### common/images.py

```python
def convert_image_to_webp(image_field, quality=85) -> ContentFile
def generate_webp_for_field(instance, source_field="image", target_field="webp_image")
```

اگر تبدیل شکست بخورد → فقط warning، فایل اصلی حفظ می‌شود. بهترین تلاش، نه بلوکه‌کننده.

### 7.2 Accounts

#### مدل Customer

```python
class Customer(AbstractBaseUser, PermissionsMixin):
    phone = models.CharField(max_length=15, unique=True, db_index=True)
    full_name = models.CharField(max_length=255, blank=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_blocked = models.BooleanField(default=False)
    date_joined = models.DateTimeField(auto_now_add=True)
    ...
    USERNAME_FIELD = "phone"
    REQUIRED_FIELDS = []
```

چرا از BaseModel ارث نمی‌برد: soft delete برای user مشکل‌ساز است (auth با is_active مدیریت می‌شود).

مدیر Customer:

- create_user(phone, password=None) — اگر password ندهید، set_unusable_password() می‌کند (مشتری عادی نمی‌تواند با password login کند).
- create_superuser(phone, password) — is_staff=True و is_superuser=True.

#### OTP (D8)

`apps/accounts/otp.py:`

```python
def generate_code() -> str:              # secrets.randbelow — cryptographic
def store_otp(*, phone, code) -> int:    # cache.set با TTL=120s
def get_otp_code(*, phone) -> str|None:
def delete_otp(*, phone) -> None:
```

فرمت ذخیره: JSON {"code": "123456"} در کلید fastfood:otp:code:0912...:v1. چرا JSON؟ آینده‌نگر برای افزودن متادیتا بدون تغییر type.

در verify:

```python
if not hmac.compare_digest(stored, code or ""):
    raise OTPInvalidError()
```

compare_digest جلوگیری از timing attack.

مصرف کد: پس از verify موفق، کد حذف می‌شود تا دوباره استفاده نشود. اگر verify شکست خورد، کد باقی می‌ماند (تا TTL).

#### محدودسازی نرخ (D9)

```python
class OTPRequestThrottle(SimpleRateThrottle):
    scope = "otp_request"  # 5/hour
    def get_cache_key(self, request, view):
        phone = request.data.get("phone")
        return f"{scope}:{phone}:{ip}"
```

کلید = phone:ip. یعنی:

- یک IP نمی‌تواند برای یک شماره بیش از ۵ بار/ساعت OTP بزند
- یک مهاجم با IP rotation می‌تواند دور بزند → اگر خواستید محکم‌تر کنید، throttle دوم per-phone (بدون IP) اضافه کنید.

`services.verify_otp` — کامل

```python
def verify_otp(*, phone, code) -> Customer:
    normalized = normalize_phone(phone)
    stored = otp_service.get_otp_code(phone=normalized)
    if stored is None:
        raise OTPExpiredError()                  # کد وجود ندارد یا TTL گذشته
    if not hmac.compare_digest(stored, code):
        raise OTPInvalidError()                  # کد اشتباه، کد پاک نمی‌شود
    otp_service.delete_otp(phone=normalized)     # مصرف شد

    customer, created = Customer.objects.get_or_create(phone=normalized)
    if created:
        customer.set_unusable_password()
        customer.save()

    if customer.is_blocked:
        raise AccountBlockedError()
    if not customer.is_active:
        raise AccountInactiveError()
    return customer
```

#### آدرس‌ها

`CustomerAddress:`

- customer FK
- address_text
- recipient_name
- recipient_phone
- is_out_of_zone (تعیین‌کننده هزینه ارسال — D10)
- is_default (UniqueConstraint روی (customer) با شرط is_default=True AND deleted_at IS NULL)

نکته‌ی کلیدی: service قبل از is_default=True کردن آدرس جدید، default قبلی را false می‌کند:

```python
if data.get("is_default"):
    CustomerAddress.objects.filter(
        customer=customer, is_default=True
    ).update(is_default=False)
```

#### یادداشت مشتری (CRM)

```python
class CustomerNote(BaseModel):
    customer = FK
    author = FK(Customer, null=True)  # کارمندی که نوشت
    text = TextField
```

یادداشت‌ها در پنل مدیر قابل مشاهده و قابل چاپ در رسید سفارش جدید هستند (در فاز بعدی؛ فعلاً فقط داده ذخیره می‌شود).

#### پروفایل ۳۶۰ درجه مشتری

`selectors.get_customer_360(customer_id):`

```python
{
    "customer": <Customer>,
    "addresses": [...],
    "notes": [...],
    "orders_count": int,
    "completed_orders_count": int,
    "lifetime_value": int,   # مجموع total_amount سفارش‌های PAID
    "last_order_at": datetime|None,
}
```

حلقه‌ی هوشمند: از django_apps.get_model("orders", "Order") با try/except استفاده می‌کند. اگر app orders نصب نباشد (در حین توسعه)، صفرها برمی‌گردد. در حال حاضر نصب است، پس واقعی می‌شود.

#### JWT

```python
def issue_tokens_for_customer(customer) -> {"access": str, "refresh": str}
def blacklist_refresh_token(refresh) -> bool  # True اگر موفق
```

`OTPVerifyView` هم session و هم JWT برمی‌گرداند:

```python
login(request._request, customer)        # session cookie
token_pair = tokens.issue_tokens_for_customer(customer)  # JWT
return Response({"user": ..., "access": ..., "refresh": ...})
```

`TokenRefreshView` (`_SimpleJWTRefreshView`):

ورودی: {"refresh": "..."}

خروجی: {"access": "...", "refresh": "..."} — چون rotation فعال است

refresh قدیمی blacklist می‌شود

استفاده‌ی دوم از refresh قدیمی → 401

`TokenLogoutView:`

ورودی: {"refresh": "..."}

خروجی: 204

refresh را blacklist می‌کند + session را هم پاک می‌کند

#### ورود کارکنان

```python
def staff_login(phone, password):
    normalized = normalize_phone(phone)          # اگر invalid → InvalidCredentialsError (no leak)
    customer = Customer.objects.get(phone=normalized)
    if customer.is_blocked: raise AccountBlockedError()
    if not customer.is_active: raise AccountInactiveError()
    if not customer.is_staff: raise NotStaffError()
    if not customer.check_password(password): raise InvalidCredentialsError()
    customer.last_login = timezone.now()
    customer.save()
```

POST /api/v1/backoffice/auth/login/ با SessionAuthentication جواب می‌دهد:

```json
{
  "user": {"id": 1, "phone": "...", "is_staff": true, ...},
  "csrf_token": "..."
}
```

### 7.3 CMS

#### RestaurantSettings (تک‌مقدار — D24)

```python
class RestaurantSettings(models.Model):
    id = models.PositiveSmallIntegerField(primary_key=True, default=1, editable=False)
    open_time = models.TimeField(default=time(11, 0))
    close_time = models.TimeField(default=time(1, 0))
    is_temporarily_closed = BooleanField(default=False)
    in_zone_delivery_fee = PositiveIntegerField(default=50_000)
    out_zone_delivery_fee = PositiveIntegerField(default=100_000)
    prep_time_buffer_minutes = PositiveSmallIntegerField(default=5)

    def save(self, *args, **kwargs):
        self.pk = 1  # هر ذخیره‌ای pk=1 را force می‌کند
        super().save(*args, **kwargs)

    def is_open(self, now=None) -> bool:
        if self.is_temporarily_closed:
            return False
        if self.open_time < self.close_time:
            return self.open_time <= now < self.close_time  # same-day
        return now >= self.open_time or now < self.close_time  # overnight
```

نکته‌ی کلیدی is_open: ساعت بسته‌شدن می‌تواند فردای ساعت باز‌شدن باشد. مثلاً 11:00 → 01:00 یعنی از ۱۱ صبح تا ۱ بامداد. الگوریتم:

اگر open < close → همون روز، بین این دو

اگر open >= close → cross-midnight: از open تا midnight، یا از midnight تا close

Singleton با save() force: حتی اگر کسی instance.pk = 42 بگذارد و save کند، دوباره pk=1 می‌شود.

Seed: migration 0002_seed_restaurant_settings.py رکورد pk=1 را در اولین migrate می‌سازد.

#### SiteSection (D23)

```python
class SiteSection(BaseModel):
    key = CharField(choices=[6 keys])
    content = JSONField(default=dict)
```

کلیدهای مجاز: hero, header, footer, announcement, lucky_wheel, about_us.

default content: DEFAULT_SITE_SECTION_CONTENT dict دارد. اگر برای key ای رکورد نباشد، selector از default استفاده می‌کند — هرگز خطای "not found" به کاربر نمی‌دهد.

UniqueConstraint: روی key با deleted_at IS NULL. یعنی می‌توانید رکورد را soft-delete کنید و دوباره با همان key بسازید، بدون conflict.

#### MediaAsset (D25)

```python
class MediaAsset(BaseModel):
    kind = CharField(choices=[("logo","Logo"),("banner","Banner"),("gallery","Gallery")])
    file = ImageField(upload_to="cms/%Y/%m/")
    webp_file = ImageField(upload_to="cms/webp/%Y/%m/", null=True, blank=True)
```

آپلود: services.create_media_asset:

- فایل اصلی را ذخیره می‌کند
- با Pillow به WebP تبدیل می‌کند
- اگر تبدیل موفق شد، webp_file را ذخیره می‌کند
- اگر شکست خورد، فقط warning — فایل اصلی همچنان کار می‌کند

بازگرداندن URL:

```python
def get_image_url(obj):
    return obj.webp_file.url if obj.webp_file else (obj.file.url if obj.file else None)
```

#### کشینگ

`get_restaurant_settings():`

- کلید: cms:restaurant_settings:v1
- TTL: 1 ساعت
- Invalidation: در update_restaurant_settings با transaction.on_commit(lambda: cache.delete(...))

`get_site_section(key):`

- کلید: cms:site_section_<key>:v1
- TTL: 1 ساعت
- Invalidation: در upsert_site_section

چرا on_commit و نه فوری؟ اگر cache را قبل از commit پاک کنیم و تراکنش rollback شود، cache خالی می‌ماند در حالی که داده هنوز قدیمی است → درخواست بعدی داده‌ی قدیمی را دوباره cache می‌کند. با on_commit، فقط بعد از commit موفق پاک می‌شود.

### 7.4 Catalog

#### دسته‌بندی

```python
class Category(BaseModel):
    name, slug, description, image, webp_image
    display_order, is_active
```

UniqueConstraint: روی slug با deleted_at IS NULL. یعنی slug پس از soft-delete قابل استفاده‌ی مجدد است.

حذف: اگر محصول زنده‌ای به category وصل باشد → CategoryHasProductsError. باید اول محصولات soft-delete شوند.

#### AddOn (D22 — لایه اول)

```python
class AddOn(BaseModel):
    name = CharField
    price = PositiveIntegerField
    is_available = BooleanField  # مدیر می‌تواند global خاموش کند
```

سناریو: آشپزخانه پنیر تمام می‌کند → مدیر is_available=False می‌کند → همه‌ی محصولات این افزودنی را از دست می‌دهند (در menu، در سفارش جدید).

#### محصول (D21)

```python
class Product(BaseModel):
    category = FK(Category)
    name, slug, description, image, webp_image
    price = PositiveIntegerField
    status = Enum: AVAILABLE / OUT_OF_STOCK / HIDDEN
    is_main_dish = BooleanField
    prep_time_minutes = PositiveSmallIntegerField
    display_order = PositiveIntegerField
```

سه حالت (D21):

- AVAILABLE: در منو دیده می‌شود، قابل خرید، در Lucky Wheel
- OUT_OF_STOCK: در منو دیده می‌شود با دکمه‌ی غیرفعال، در Lucky Wheel نیست، سفارش جدید نمی‌پذیرد
- HIDDEN: از منو و Lucky Wheel کاملاً حذف

بدون Variant (D20): «پیتزا مارگاریتا تک‌نفره» و «دو‌نفره» = دو رکورد جدا با slug، قیمت، عکس، prep_time مستقل.

is_main_dish:

- True → غذای اصلی، در Lucky Wheel
- False → پیش‌غذا/نوشیدنی/افزودنی، در پیشنهاد upsell سبد خرید (سمت فرانت)

#### ProductAddOn (D22 — لایه دوم)

```python
class ProductAddOn(BaseModel):
    product = FK(Product)
    addon = FK(AddOn)
    min_quantity = PositiveSmallIntegerField(default=0)
    max_quantity = PositiveSmallIntegerField(default=5)
```

CheckConstraint: min_quantity <= max_quantity در سطح DB.

UniqueConstraint: روی (product, addon) با deleted_at IS NULL — یک محصول نمی‌تواند دو لینک به همان add-on داشته باشد (اما می‌تواند قبلی را soft-delete و جدید بسازد).

در عمل:

- AddOn «پنیر اضافه» ساخته می‌شود (price=20k، global)
- برای «پیتزا مارگاریتا»: ProductAddOn(addon=پنیر, min=0, max=3)
- برای «برگر»: ProductAddOn(addon=پنیر, min=0, max=2)

مشتری می‌تواند تا ۳ عدد پنیر برای پیتزا انتخاب کند، تا ۲ برای برگر.

#### کش منو

`get_storefront_menu():`

- کلید: catalog:storefront_menu:v1
- TTL: 1 ساعت
- Query: categories → prefetch_related(products excluding HIDDEN) — فقط ۲–۳ کوئری

OUT_OF_STOCK شامل است (طبق spec)، HIDDEN نه.

ساختار پاسخ:

```json
{
  "categories": [
    {
      "id": 1, "name": "پیتزا", "image_url": "...",
      "products": [
        {"id": 1, "name": "مارگاریتا", "price": 150000,
         "status": "AVAILABLE", "is_main_dish": true, "image_url": "..."}
      ]
    }
  ]
}
```

Cache-safe: به‌جای pickle کردن model instance، selector مستقیماً dict می‌سازد. چرا؟ چون تغییرات schema بین دو deploy باعث می‌شوند pickle قدیمی با کد جدید ناسازگار شود.

#### گردونه شانس

`get_lucky_wheel_products(category_slug=None):`

فقط AVAILABLE + is_main_dish=True + category.is_active=True

می‌تواند بر اساس ?category=slug فیلتر شود

کش جدا (per category): catalog:lucky_wheel:v1 و catalog:lucky_wheel:pizzas:v1

منطق چرخش روی فرانت است. backend فقط لیست را می‌دهد. spec صریحاً گفت که load اضافی ایجاد نکنیم.

#### جزئیات محصول (بدون کش)

`get_storefront_product(slug):`

- select_related("category")
- prefetch_related(addon_links با select_related("addon"))
- فقط addon_links که addon.is_available=True هستند برمی‌گردند

پاسخ:

```json
{
  "id": 1, "name": "مارگاریتا", "price": 150000,
  "category": {...}, "addons": [
    {"addon_id": 1, "name": "پنیر اضافه", "price": 20000,
     "min_quantity": 0, "max_quantity": 3}
  ]
}
```

### 7.5 Orders

#### ماشین حالت (قلب پروژه)

```text
                          ┌──────────────────────┐
                          │  PENDING_PAYMENT     │  payment=UNPAID
                          │  (15 min timeout)    │
                          └──────────┬───────────┘
                    ┌────────────────┼────────────────┐
             پرداخت موفق        پرداخت ناموفق      15 دقیقه گذشت
                    ↓                ↓                 ↓
            ┌───────────────┐   (در PENDING می‌ماند)  CANCELED
            │  PROCESSING   │  payment=PAID
            │  daily_number │
            └───────┬───────┘
                    │ مدیر mark-ready
                    ↓
            ┌───────────────┐
            │     READY     │  → SMS به مشتری
            └───────┬───────┘
                    │ مدیر mark-completed
                    ↓
            ┌───────────────┐
            │   COMPLETED   │  (آرشیو)
            └───────────────┘
```

مدیر cancel (از هر stage فعال به‌جز COMPLETED/CANCELED):

- PAID → CANCELED + payment=AWAITING_REFUND
- UNPAID → CANCELED + payment=UNPAID

مدیر refund (از AWAITING_REFUND):

- → payment=REFUNDED (با ثبت card_number و tracking_code)

#### مدل Order

```python
class Order(BaseModel):
    customer = FK(Customer)
    status, payment_status, delivery_type
    delivery_address = FK(CustomerAddress, null=True)
    delivery_address_snapshot, delivery_recipient_name, delivery_recipient_phone
    subtotal, delivery_fee, total_amount
    prep_time_minutes, expected_ready_at
    paid_at
    notes_to_kitchen
    is_printed, printed_at
    daily_number, daily_number_date
    expires_at
    canceled_at, cancellation_reason, canceled_by
    refund_card_number, refund_tracking_code, refunded_at, refunded_by
```

delivery_address_snapshot: حتی اگر آدرس بعداً ویرایش یا soft-delete شود، فاکتور دست‌نخورده باقی می‌ماند.

`OrderItem / OrderItemAddOn` (snapshot — spec §D)

```python
class OrderItem(BaseModel):
    order, product
    product_name_snapshot = CharField
    unit_price_snapshot = PositiveIntegerField
    quantity
    addons_total, line_total


class OrderItemAddOn(BaseModel):
    order_item, addon
    addon_name_snapshot
    unit_price_snapshot
    quantity
    line_total
```

چرا snapshot؟ اگر مدیر قیمت پیتزا را فردا از 150k به 200k تغییر دهد، فاکتورهای دیروز نباید تغییر کنند. snapshot این را تضمین می‌کند.

#### ایجاد سفارش (services.create_order)

```python
def create_order(*, customer, delivery_type, address_id, items, notes_to_kitchen=""):
    _ensure_restaurant_is_open()                        # RestaurantClosedError اگر بسته
    # validated delivery_type
    address = _resolve_address(customer, address_id)    # NotFoundError اگر متعلق به کاربر نیست
    # delivery_fee: PICKUP=0، DELIVERY با is_out_of_zone → in/out_zone_fee

    prep_time = _compute_prep_time(items, product_by_id)  # max(item.prep) + buffer
    order = Order.objects.create(
        status=PENDING_PAYMENT,
        payment_status=UNPAID,
        expires_at=now + timedelta(minutes=15),
        ...
    )
    subtotal = _build_order_items(order, items)         # validates product + addon availability
    order.subtotal = subtotal
    order.total_amount = subtotal + delivery_fee
    order.save()
```

`_build_order_items` — validationها:

- محصول باید وجود داشته باشد (ProductNotFound)
- محصول نباید HIDDEN باشد
- محصول باید AVAILABLE باشد (نه OUT_OF_STOCK)
- دسته‌ی محصول باید is_active=True باشد
- افزودنی باید برای این محصول تعریف شده باشد (ProductAddOn)
- افزودنی باید addon.is_available=True باشد
- 0 <= addon.quantity <= link.max_quantity
- اگر هر کدام شکست خورد → ValidationError با details مشخص.

#### زمان آماده‌سازی (D12)

```python
def _compute_prep_time(items, product_by_id) -> int:
    max_prep = max(item.product.prep_time_minutes for item in items)
    buffer = RestaurantSettings.prep_time_buffer_minutes  # default 5
    return max_prep + buffer
```

مثال: پیتزا ۱۵ دقیقه، نوشابه ۰ دقیقه → max = 15، + buffer 5 = 20.

#### شماره روزانه (D7)

`mark_order_paid` (که از payments.verify_payment صدا زده می‌شود):

```python
def _assign_daily_number(order):
    today = timezone.localdate()                    # بر اساس Asia/Tehran
    key = f"order_seq:{today.isoformat()}"
    redis = get_redis()
    for attempt in range(10):
        number = int(redis.incr(key))
        if number == 1:
            redis.expire(key, 60*60*48)             # 48h TTL برای پاکسازی
        order.daily_number = number
        order.daily_number_date = today
        try:
            order.save(update_fields=["daily_number", "daily_number_date", "updated_at"])
            return
        except IntegrityError:
            continue                                # collision → retry
    raise RuntimeError(...)
```

چرا Redis INCR؟ atomic، سریع، بدون lock. چرا retry روی IntegrityError؟ اگر Redis ری‌ست شود (dev یا crash)، شماره‌ها از ۱ شروع می‌شوند و ممکن است با رکوردهای قبلی هم‌روز تصادم کنند. UniqueConstraint((daily_number_date, daily_number)) تصادم را می‌گیرد و retry می‌کند.

`mark_order_paid` — تراکنش کامل

```python
@transaction.atomic
def mark_order_paid(*, order_id, paid_at=None) -> Order:
    order = Order.objects.select_for_update().get(pk=order_id)
    if order.status != PENDING_PAYMENT:
        raise OrderStateError()

    now = paid_at or timezone.now()
    order.paid_at = now
    order.status = PROCESSING
    order.payment_status = PAID
    order.expected_ready_at = now + timedelta(minutes=order.prep_time_minutes)
    order.is_printed = False
    order.save(...)

    _assign_daily_number(order)                     # داخل همان تراکنش
    transaction.on_commit(lambda: send_order_registered_sms.delay(order.pk))
    return order
```

نکته: SMS فقط بعد از commit — اگر commit شکست بخورد، SMS ارسال نمی‌شود.

#### Live POS (D13)

`get_live_orders():`

```python
Order.objects.filter(status__in=[PROCESSING, READY]).order_by("expected_ready_at")
```

فرانت هر ۱۰–۱۵ ثانیه این را poll می‌کند. سفارش‌های is_printed=False → آلارم + چاپ. بعد از چاپ، فرانت POST /orders/<id>/mark-printed/ صدا می‌زند.

#### لغو خودکار (D — ۱۵ دقیقه)

```python
cancel_expired_unpaid_orders هر ۶۰ ثانیه توسط Celery Beat اجرا می‌شود:
```

```python
expired = Order.objects.select_for_update().filter(
    status=PENDING_PAYMENT,
    expires_at__lt=timezone.now(),
)
for order in expired:
    order.status = CANCELED
    order.canceled_at = timezone.now()
    order.cancellation_reason = "auto: payment timeout"
    order.save()
```

چرا Beat و نه apply_async(countdown=900)؟ اگر worker crash کند، countdown از دست می‌رود و سفارش هیچ‌وقت لغو نمی‌شود. Beat idempotent است و دوباره تلاش می‌کند.

#### تغییر زمان آماده‌سازی

`update_prep_time(order_id, new_prep_time_minutes):`

فقط در PROCESSING یا READY مجاز

expected_ready_at از paid_at بازمحاسبه می‌شود (نه از now())

transaction.on_commit(send_prep_time_changed_sms.delay(...))

چرا از paid_at؟ اگر از now() محاسبه شود، مدیر می‌تواند هر بار با تغییر prep time، ETA را به تعویق بیندازد. از paid_at محاسبه شده تا زمان پرداخت پایه باشد.

### 7.6 Payments

#### ZarinpalClient (v4)

```python
class ZarinpalClient:
    def __init__(self, merchant_id=None, sandbox=None):
        base = "sandbox" if sandbox else "payment"
        self.request_url = f"https://{base}.zarinpal.com/pg/v4/payment/request.json"
        self.verify_url  = f"https://{base}.zarinpal.com/pg/v4/payment/verify.json"
        self.startpay_url = f"https://{base}.zarinpal.com/pg/StartPay"

    def request_payment(*, amount, description, callback_url=None) -> dict:
        # POST → {"data": {"code": 100, "authority": "S..."}}
        # اگر code != 100 → ZarinpalRequestError

    def verify_payment(*, amount, authority) -> dict:
        # POST → {"data": {"code": 100 یا 101, "ref_id": "..."}}
        # 100 = موفق تازه، 101 = قبلاً تأیید شده (idempotent)
        # هر code دیگه → ZarinpalVerifyError

    def build_redirect_url(authority) -> str:
        return f"{self.startpay_url}/{authority}"
```

urllib به‌جای requests: بدون dependency اضافی. کنترل کامل روی timeout و exception.

#### مدل Payment

```python
class Payment(BaseModel):
    order = FK(Order, PROTECT)
    amount = PositiveIntegerField
    status = Enum: PENDING / SUCCEEDED / FAILED / CANCELED
    authority = CharField (unique per alive)
    ref_id = CharField (خالی تا verify)
    gateway_response_code, gateway_response_message
    verified_at, failed_at, canceled_at
```

UniqueConstraint روی authority با deleted_at IS NULL: یک authority در یک لحظه فقط یک Payment زنده دارد.

`start_payment_for_order`

```python
def start_payment_for_order(*, order):
    if order.status != PENDING_PAYMENT: raise OrderStateError()
    if order.payment_status != UNPAID: raise OrderStateError()
    if order.expires_at < now: raise OrderStateError("مهلت پرداخت تمام شده")

    revalidate_order_for_payment(order)  # restaurant open + product/addon available

    client = ZarinpalClient()
    gateway_data = client.request_payment(amount=order.total_amount, description=...)
    authority = gateway_data["authority"]

    Payment.objects.create(order=order, amount=..., status=PENDING, authority=authority)

    return {
        "payment_url": client.build_redirect_url(authority),
        "authority": authority,
        "amount": order.total_amount,
    }
```

#### verify_payment — idempotent (کلیدی!)

```python
@transaction.atomic
def verify_payment(*, authority, status):
    payment = Payment.objects.select_for_update().get(authority=authority)

    if payment.status == SUCCEEDED:
        return payment                    # idempotent: callback تکراری
    if payment.status in {FAILED, CANCELED}:
        raise PaymentNotVerifiableError()

    if status != "OK":
        payment.status = FAILED
        payment.save()
        return payment

    try:
        verify_data = client.verify_payment(amount=payment.amount, authority=authority)
    except ZarinpalVerifyError:
        payment.status = FAILED
        payment.save()
        raise

    payment.status = SUCCEEDED
    payment.ref_id = verify_data["ref_id"]
    payment.verified_at = now
    payment.save()

    mark_order_paid(order_id=payment.order_id, paid_at=payment.verified_at)
    return payment
```

چرا select_for_update()؟ اگر دو callback هم‌زمان برسند (Zarinpal retries)، اولی lock می‌گیرد، verify می‌کند، commit می‌شود. دومی بعد از release، payment.status == SUCCEEDED را می‌بیند و بدون verify دوم برمی‌گردد → no double order transition.

چرا verify + mark_order_paid در یک transaction.atomic؟ اگر mark_order_paid fail شود (مثلاً OrderStateError)، Payment هم rollback می‌شود و در PENDING می‌ماند. پس reverify_pending_payments بعداً دوباره تلاش می‌کند.

`code == 101`: زرین‌پال این را "قبلاً تأیید شده" برمی‌گرداند. ما با verify_data که ref_id دارد، آن را موفق می‌گیریم.

#### وظیفه باز-تأیید (پشتیبان)

```python
reverify_pending_payments هر ۵ دقیقه:
```

```python
for payment in Payment.objects.filter(status=PENDING, created_at__lt=now-3min):
    try:
        verify_payment(authority=payment.authority, status="OK")
    except Exception:
        logger.warning(...)  # در دور بعد دوباره
```

سناریو: کاربر پرداخت کرد، ولی callback به هر دلیل (شبکه، restart) نرسید. این task پرداخت‌های PENDING قدیمی‌تر از ۳ دقیقه را دوباره verify می‌کند. زرین‌پال verify idempotent است، پس هیچ خطری ندارد.

#### جریان بازپرداخت (D11)

مدیر POST /orders/<id>/cancel/ → cancel_order_by_manager

- از PROCESSING/READY: status=CANCELED, payment=AWAITING_REFUND
- از PENDING: status=CANCELED, payment=UNPAID

مدیر دستی پول را برمی‌گرداند (کارت‌به‌کارت)

مدیر POST /orders/<id>/refund/ با {card_number, tracking_code} → record_refund

payment=REFUNDED، ثبت card و tracking

## 8. احراز هویت و مجوزها

### جدول کامل

| Endpoint | Auth | Permission | CSRF |
| --- | --- | --- | --- |
| POST /storefront/auth/otp/request/ | — | AllowAny | ✗ |
| POST /storefront/auth/otp/verify/ | — | AllowAny | ✗ |
| POST /storefront/auth/token/refresh/ | — | AllowAny | ✗ |
| POST /storefront/auth/token/logout/ | — | AllowAny | ✗ |
| POST /storefront/auth/logout/ | Session | IsAuthenticated | ✓ |
| GET /storefront/auth/me/ | JWT یا Session | IsAuthenticated | — |
| POST /backoffice/auth/login/ | — | AllowAny | ✗ |
| POST /backoffice/auth/logout/ | Session | IsStaffUser | ✓ |
| همه‌ی Backoffice محافظت‌شده | Session فقط | IsStaffUser | ✓ |

### الگوی Storefront

فرانت وب (SPA) → JWT:

```text
Authorization: Bearer <access>
```

(هیچ CSRF نیاز نیست، چون هدر Authorization خودش anti-CSRF است)

مرورگر سنتی → Session:

```text
Cookie: sessionid=...
Header: X-CSRFToken: ...
```

هر دو با هم کار می‌کنند. JWTAuthentication اول چک می‌شود؛ اگر هدر Authorization نبود، SessionAuthentication fallback است.

### الگوی Backoffice (چرا Session فقط — D4)

```python
class BackofficeAPIView(APIView):
    authentication_classes = [SessionAuthentication]
```

اگر مهاجم JWT مشتری را داشته باشد و مشتری هم اتفاقاً staff باشد — JWT بازهم رد می‌شود، چون session cookie لازم است. این defense-in-depth است.

تست: `test_jwt_rejected_on_backoffice` این را تأیید می‌کند.

### CSRF — چه زمانی لازم است؟

| روش auth | CSRF |
| --- | --- |
| JWT (هدر Authorization) | ✗ |
| Session (cookie) | ✓ برای POST/PATCH/DELETE |

چرا؟ CSRF attack با ارسال کوکی خودکار اتفاق می‌افتد. JWT در هدر دستی است، پس مهاجم نمی‌تواند از سایت خودش آن را ارسال کند.

## 9. مرجع کامل API

### 9.1 Storefront

#### احراز هویت

| Method | Path | Auth | Body / Params |
| --- | --- | --- | --- |
| GET | /auth/csrf/ | — | — |
| POST | /auth/otp/request/ | — | {phone} |
| POST | /auth/otp/verify/ | — | {phone, code} → {user, access, refresh} |
| POST | /auth/token/refresh/ | — | {refresh} → {access, refresh} |
| POST | /auth/token/logout/ | — | {refresh} → 204 |
| POST | /auth/logout/ | Session | — |
| GET | /auth/me/ | ✓ | — |
| GET/POST | /auth/addresses/ | ✓ | {address_text, recipient_name?, is_out_of_zone?, is_default?} |
| GET/PATCH/DELETE | /auth/addresses/<id>/ | ✓ | — |

#### کاتالوگ

| Method | Path | Auth | Params |
| --- | --- | --- | --- |
| GET | /catalog/menu/ | — | — |
| GET | /catalog/lucky-wheel/ | — | ?category=slug |
| GET | /catalog/products/<slug>/ | — | — |

#### سفارش‌ها

| Method | Path | Auth | Body |
| --- | --- | --- | --- |
| GET | /orders/ | ✓ | — |
| POST | /orders/ | ✓ | {delivery_type, address_id?, notes_to_kitchen?, items: [{product_id, quantity, addons?: [{addon_id, quantity}]}]} |
| GET | /orders/<id>/ | ✓ | — |

#### پرداخت‌ها

| Method | Path | Auth | Body |
| --- | --- | --- | --- |
| POST | /payments/request/ | ✓ | {order_id} → {payment_url, authority, amount} |
| POST | /payments/retry/ | ✓ | {order_id} → {payment_url, authority, amount} |
| GET | /payments/callback/ | — | ?Authority=X&Status=OK|NOK[&format=json] |
| GET | /payments/status/<authority>/ | ✓ | — |

#### CMS

| Method | Path | Auth |
| --- | --- | --- |
| GET | /cms/restaurant-status/ | — |
| GET | /cms/site-sections/ | — |
| GET | /cms/site-sections/<key>/ | — |
| GET | /cms/media-assets/?kind=banner | — |

### 9.2 Backoffice

#### احراز هویت

| Method | Path | Body |
| --- | --- | --- |
| GET | /auth/csrf/ | — |
| POST | /auth/login/ | {phone, password} → {user, csrf_token} |
| POST | /auth/logout/ | — |
| GET | /auth/me/ | — |

#### CRM

| Method | Path | Body |
| --- | --- | --- |
| GET | /crm/customers/?search=&is_blocked= | — |
| GET | /crm/customers/<id>/ | — |
| PATCH | /crm/customers/<id>/ | {full_name?, is_blocked?, is_active?} |
| GET/POST | /crm/customers/<id>/notes/ | {text} |
| DELETE | /crm/customers/<id>/notes/<note_id>/ | — |

#### کاتالوگ

| Method | Path | Body |
| --- | --- | --- |
| GET/POST | /catalog/categories/ | {name, slug, description?, display_order?, is_active?} |
| GET/PATCH/DELETE | /catalog/categories/<id>/ | — |
| POST | /catalog/categories/<id>/image/ | multipart image |
| GET/POST | /catalog/addons/ | {name, price, is_available?} |
| GET/PATCH/DELETE | /catalog/addons/<id>/ | — |
| GET/POST | /catalog/products/?category_id=&status=&is_main_dish=&search= | {name, slug, category_id, price, status?, is_main_dish?, prep_time_minutes?, addons?} |
| GET/PATCH/DELETE | /catalog/products/<id>/ | — |
| POST | /catalog/products/<id>/image/ | multipart image |
| GET/PUT | /catalog/products/<id>/addons/ | {addons: [{addon_id, min_quantity, max_quantity}]} |

#### سفارش‌ها

| Method | Path | Body |
| --- | --- | --- |
| GET | /orders/?status=&payment_status=&delivery_type=&search=&date_from=&date_to= | — |
| GET | /orders/live/ | — |
| GET | /orders/<id>/ | — |
| POST | /orders/<id>/mark-ready/ | — |
| POST | /orders/<id>/mark-completed/ | — |
| POST | /orders/<id>/mark-printed/ | — |
| POST | /orders/<id>/cancel/ | {reason?} |
| PATCH | /orders/<id>/prep-time/ | {prep_time_minutes} |
| POST | /orders/<id>/refund/ | {card_number, tracking_code} |

#### پرداخت‌ها

| Method | Path |
| --- | --- |
| GET | /payments/orders/<order_id>/payments/ |

#### CMS

| Method | Path | Body |
| --- | --- | --- |
| GET/PATCH | /cms/restaurant-settings/ | {open_time?, close_time?, is_temporarily_closed?, in_zone_delivery_fee?, out_zone_delivery_fee?, prep_time_buffer_minutes?} |
| GET | /cms/site-sections/ | — |
| GET/PUT | /cms/site-sections/<key>/ | {content: {...}} |
| GET/POST | /cms/media-assets/?kind= | multipart {kind, file, title?, alt_text?} |
| GET/PATCH/DELETE | /cms/media-assets/<id>/ | {title?, alt_text?} |

### 9.3 Global

| Method | Path |
| --- | --- |
| GET | /health/ |
| GET | /api/v1/storefront/schema/ و /docs/ |
| GET | /api/v1/backoffice/schema/ و /docs/ (staff only) |

## 10. عیب‌یابی

| علامت | علت | راه‌حل |
| --- | --- | --- |
| no such table: accounts_customer | migrate اجرا نشده | python manage.py migrate |
| 500 روی OTP request | Redis بالا نیست | redis-cli ping یا docker start fastfood-redis |
| 403 CSRF Failed | هدر X-CSRFToken فراموش شده | GET /auth/csrf/ و هدر را بفرستید |
| 401 Not authenticated | session ندارید یا JWT منقضی | OTP دوباره یا refresh کنید |
| 409 RestaurantClosedError | خارج از ساعت | PATCH restaurant-settings ساعت را گسترده کنید |
| OTP در console نمی‌آید | SMS_IR_API_KEY پر است | خالی کنید |
| NOT_STAFF در login backoffice | user is_staff=False | python manage.py create_staff <phone> <pass> --superuser |
| refresh کار نمی‌کند | migration token_blacklist اجرا نشده | python manage.py migrate |
| JWT rejected on backoffice | درست است — by design | از session استفاده کنید |
| test_*.py fail روی Redis | DB 15 کانفیگ شده ولی Redis بالا نیست | Redis را بالا بیاورید |
| billiard PermissionError در Celery | pool پیش‌فرض روی Windows | -P solo یا -P threads |
| Celery Ctrl+C کار نمی‌کند | باگ Celery 5.4 | ارتقا به celery>=5.5 یا -P solo |
| migrate به SQLite دیگری می‌رود | دو فایل db.sqlite3 | Get-ChildItem -Recurse -Filter db.sqlite3 |
| daily_number صفر می‌ماند | پرداخت موفق mark نشده | Payment.verify_payment را چک کنید |

## 11. چک‌لیست نهایی

هدف: از صفر به یک بک‌اند کامل تست‌شده در ~۳۰ دقیقه.

پیش‌نیاز: Redis روی 127.0.0.1:6379 در حال اجرا، .env طبق بخش ۴، settings_sqlite.py موجود.

### مرحله ۰ — راه‌اندازی

```powershell
python manage.py migrate --settings=config.settings_sqlite
python manage.py create_staff 09123456789 "Test@1234" --superuser --settings=config.settings_sqlite
python manage.py runserver --settings=config.settings_sqlite
```

- [ ] migrate بدون خطا تمام شد
- [ ] create_staff پیام Created superuser user: 09123456789 چاپ کرد
- [ ] runserver روی http://127.0.0.1:8000 بالا آمد

### مرحله ۱ — Health & Docs

```bash
curl http://127.0.0.1:8000/health/
```

- [ ] پاسخ: {"success": true, "data": {"status": "ok"}}
- [ ] مرورگر: http://127.0.0.1:8000/api/v1/storefront/docs/ باز می‌شود (لیست endpointها)

### مرحله ۲ — OTP Flow (مشتری)

```text
POST /api/v1/storefront/auth/otp/request/
Content-Type: application/json

{"phone": "09120000000"}
```

- [ ] پاسخ: {"message": "کد تایید ارسال شد.", "expires_in": 120}
- [ ] در console runserver خط کد تایید شما: NNNNNN دیده می‌شود — کد را بردارید

```text
POST /api/v1/storefront/auth/otp/verify/
Content-Type: application/json

{"phone": "09120000000", "code": "NNNNNN"}
```

- [ ] پاسخ شامل user, access, refresh است

### مرحله ۳ — Session تست

```text
GET /api/v1/storefront/auth/me/
```

- [ ] با cookie session، پاسخ {"id": 1, "phone": "09120000000", ...} است

### مرحله ۴ — JWT تست

- [ ] کپی access از پاسخ مرحله ۲
- [ ] یک tab جدید Postman، بدون cookie

```text
GET /api/v1/storefront/auth/me/
Authorization: Bearer <access>
```

- [ ] پاسخ ۲۰۰ با همان user

### مرحله ۵ — Refresh تست

```text
POST /api/v1/storefront/auth/token/refresh/
{"refresh": "<refresh از مرحله ۲>"}
```

- [ ] پاسخ شامل access و refresh جدید است
- [ ] refresh جدید متفاوت از قبلی است (rotation)
- [ ] همان refresh قدیمی را دوباره refresh کنید → ۴۰۱

### مرحله ۶ — Backoffice Login

```text
POST /api/v1/backoffice/auth/login/
{"phone": "09123456789", "password": "Test@1234"}
```

- [ ] پاسخ ۲۰۰ با user.is_staff: true و csrf_token
- [ ] از این لحظه، JWT مشتری در یک tab جدید کار نمی‌کند روی backoffice:

```text
GET /api/v1/backoffice/orders/
Authorization: Bearer <access مشتری>
```

- [ ] پاسخ ۴۰۱ یا ۴۰۳ (تأیید D4)

### مرحله ۷ — ساخت Category

```text
POST /api/v1/backoffice/catalog/categories/
X-CSRFToken: <csrf از login>
Content-Type: application/json

{"name": "پیتزا", "slug": "pizzas", "display_order": 1}
```

- [ ] ۲۰۱ با id: 1

### مرحله ۸ — ساخت AddOn

```text
POST /api/v1/backoffice/catalog/addons/
X-CSRFToken: <csrf>

{"name": "پنیر اضافه", "price": 20000}
```

- [ ] ۲۰۱ با id: 1

### مرحله ۹ — ساخت Product

```text
POST /api/v1/backoffice/catalog/products/
X-CSRFToken: <csrf>

{
  "name": "مارگاریتا - تک نفره",
  "slug": "margherita-single",
  "category_id": 1,
  "price": 150000,
  "is_main_dish": true,
  "prep_time_minutes": 15,
  "status": "AVAILABLE",
  "addons": [{"addon_id": 1, "min_quantity": 0, "max_quantity": 3}]
}
```

- [ ] ۲۰۱ با id: 1 و addons: [{"addon_id": 1, ...}]

### مرحله ۱۰ — Menu (public)

```text
GET /api/v1/storefront/catalog/menu/
```

- [ ] categories[0].products[0].name == "مارگاریتا - تک نفره"

### مرحله ۱۱ — Lucky Wheel

```text
GET /api/v1/storefront/catalog/lucky-wheel/
```

- [ ] products شامل مارگاریتا است

### مرحله ۱۲ — Product Detail

```text
GET /api/v1/storefront/catalog/products/margherita-single/
```

- [ ] پاسخ شامل addons: [{"addon_id": 1, "name": "پنیر اضافه", "price": 20000, "min_quantity": 0, "max_quantity": 3}]

### مرحله ۱۳ — افزودن Address (به‌عنوان مشتری)

برگردید به tab مشتری (session یا JWT):

```text
POST /api/v1/storefront/auth/addresses/
Authorization: Bearer <access مشتری>
Content-Type: application/json

{
  "address_text": "تهران، خیابان ولیعصر، پلاک ۱۰",
  "recipient_name": "علی رضایی",
  "recipient_phone": "09120000000",
  "is_out_of_zone": false,
  "is_default": true
}
```

- [ ] ۲۰۱

### مرحله ۱۴ — ساخت Order

```text
POST /api/v1/storefront/orders/
Authorization: Bearer <access>

{
  "delivery_type": "PICKUP",
  "notes_to_kitchen": "بدون پیاز",
  "items": [
    {"product_id": 1, "quantity": 2, "addons": [{"addon_id": 1, "quantity": 1}]}
  ]
}
```

- [ ] ۲۰۱ با:
  - status: "PENDING_PAYMENT"
  - payment_status: "UNPAID"
  - subtotal: 320000 (150000*2 + 20000*1)
  - total_amount: 320000
  - prep_time_minutes: 20 (15 + 5 buffer)
  - expires_at حدوداً ۱۵ دقیقه بعد
- [ ] id را ذخیره کنید (مثلاً 1)

### مرحله ۱۵ — Payment Request (بدون Zarinpal واقعی)

چون ZARINPAL_MERCHANT_ID خالی است، این endpoint با خطا برمی‌گردد. اما منطقش تست‌شده است. برای تست دستی موفق پرداخت، از shell استفاده کنید:

```powershell
python manage.py shell --settings=config.settings_sqlite -c "
from apps.orders.models import Order
from apps.orders.services import mark_order_paid
from apps.payments.models import Payment
from django.utils import timezone

o = Order.objects.get(pk=1)
Payment.objects.create(
    order=o, amount=o.total_amount, status='SUCCEEDED',
    authority='DEV-AUTH-1', ref_id='DEV-REF-1',
    verified_at=timezone.now(),
)
o = mark_order_paid(order_id=1)
print(f'status={o.status}, payment={o.payment_status}, daily={o.daily_number}')
"
```

- [ ] خروجی: status=PROCESSING, payment=PAID, daily=1

### مرحله ۱۶ — Order Tracking (مشتری)

```text
GET /api/v1/storefront/orders/1/
Authorization: Bearer <access>
```

- [ ] status: "PROCESSING", daily_number: 1, expected_ready_at: <ISO datetime>

### مرحله ۱۷ — Live POS (ادمین)

با session backoffice:

```text
GET /api/v1/backoffice/orders/live/
Cookie: sessionid=<...>
```

- [ ] پاسخ آرایه‌ای شامل سفارش شما با is_printed: false
- [ ] مرتب بر اساس expected_ready_at

### مرحله ۱۸ — Mark Printed

```text
POST /api/v1/backoffice/orders/1/mark-printed/
X-CSRFToken: <csrf>
```

- [ ] is_printed: true و printed_at پر شده

### مرحله ۱۹ — Mark Ready (SMS به مشتری)

```text
POST /api/v1/backoffice/orders/1/mark-ready/
```

- [ ] status: "READY"
- [ ] در console runserver خط ارسال SMS (اگر SMS_IR_API_KEY خالی، به‌عنوان warning)

### مرحله ۲۰ — Override Prep Time

```text
PATCH /api/v1/backoffice/orders/1/prep-time/
{"prep_time_minutes": 25}
```

- [ ] prep_time_minutes: 25، expected_ready_at بازمحاسبه شده (paid_at + 25min)

### مرحله ۲۱ — Mark Completed

```text
POST /api/v1/backoffice/orders/1/mark-completed/
```

- [ ] status: "COMPLETED"

### مرحله ۲۲ — Refund Flow (سفارش دوم)

سفارش دوم بسازید (مراحل ۱۴–۱۵ با order_id=2):

- [ ] سفارش دوم PROCESSING است

```text
POST /api/v1/backoffice/orders/2/cancel/
{"reason": "customer request"}
```

- [ ] status: "CANCELED", payment_status: "AWAITING_REFUND"

```text
POST /api/v1/backoffice/orders/2/refund/
{"card_number": "6037-1234-5678-9012", "tracking_code": "123456789"}
```

- [ ] payment_status: "REFUNDED", refund_tracking_code: "123456789"

### مرحله ۲۳ — CRM

```text
GET /api/v1/backoffice/crm/customers/1/
```

- [ ] orders_count: 2, lifetime_value: 320000 (فقط سفارش PAID حساب می‌شود — سفارش دوم REFUNDED است، پس ممکن است lifetime_value: 320000 باشد و completed_orders_count: 1)

```text
POST /api/v1/backoffice/crm/customers/1/notes/
{"text": "مشتری VIP"}
```

- [ ] ۲۰۱ با author_phone

### مرحله ۲۴ — CMS Settings

```text
PATCH /api/v1/backoffice/cms/restaurant-settings/
{"in_zone_delivery_fee": 60000, "prep_time_buffer_minutes": 7}
```

- [ ] ۲۰۰ با مقادیر جدید

```text
GET /api/v1/storefront/cms/restaurant-status/
```

- [ ] in_zone_delivery_fee: 60000

### مرحله ۲۵ — CMS Site Section

```text
PUT /api/v1/backoffice/cms/site-sections/hero/
{"content": {"title": "سلام", "subtitle": "خوش آمدید"}}
```

- [ ] ۲۰۰

```text
GET /api/v1/storefront/cms/site-sections/hero/
```

- [ ] content.title == "سلام"

### مرحله ۲۶ — Rate Limit OTP

```text
POST /api/v1/storefront/auth/otp/request/  (× 6 بار سریع)
{"phone": "09129999999"}
```

- [ ] بار ششم → 429 Too Many Requests با envelope {"success": false, "error": {"code": "THROTTLED", ...}}

### مرحله ۲۷ — Authorization Isolation

بدون login، backoffice را بزنید:

```text
GET /api/v1/backoffice/orders/
```

- [ ] ۴۰۱ یا ۴۰۳

به‌عنوان مشتری، سفارش دیگران:

```text
GET /api/v1/storefront/orders/999/
Authorization: Bearer <access مشتری>
```

- [ ] ۴۰۴ ORDER_NOT_FOUND

### مرحله ۲۸ — اجرای تست‌های خودکار

```powershell
pytest -v
```

- [ ] همه‌ی تست‌ها PASS
- [ ] حداقل ۴۰ تست (accounts, orders, payments, catalog, cms, jwt, permissions, n+1, e2e)

### مرحله ۲۹ — Production Check

```powershell
$env:DEBUG="False"
python manage.py check --deploy
```

- [ ] System check identified no issues (0 silenced).
- [ ] اگر SECRET_KEY dev بود، خطای common.E001 → در .env تغییر دهید

## جمع‌بندی

اگر همه‌ی مراحل بالا را تیک زدید:

✅ بک‌اند کامل کار می‌کند — از OTP تا پرداخت، از Live POS تا Refund و CRM و CMS.

### کارهای باقی‌مانده برای production واقعی

- تنظیم secrets و production env
- راه‌اندازی Redis و Celery workers با config production
- فعال‌سازی HTTPS و domainها
- بررسی rate limits و monitoring
- اسکریپت backup و deploy pipeline
