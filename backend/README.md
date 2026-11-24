# Comprehensive Project Documentation — FastFood Backend

This document is a complete guide from zero to one hundred: why each module exists, how it works, and at the end a complete checklist to verify backend functionality.

How to use it: if you are new to the project, read section 1 in order. If you want to test quickly, go to section 10 (final checklist). If you find a bug, section 9 (Troubleshooting) answers most problems.

Versioning: this document describes the state after Phase 9 (JWT + Backoffice Session).

## Table of Contents

- Project overview
- Folder structure
- Technology stack and key decisions
- Quick setup (Local)
- Configuration and environment variables
- Request flow architecture
- Modules in detail
- 7.1 Common
- 7.2 Accounts
- 7.3 CMS
- 7.4 Catalog
- 7.5 Orders
- 7.6 Payments
- Authentication and authorization
- Complete API reference
- Troubleshooting
- Final checklist (full backend test)

## 1. Project Overview

The backend is a single-branch fast-food restaurant with two completely separate API areas:

| Area | Path | User | Authentication |
| --- | --- | --- | --- |
| Storefront | /api/v1/storefront/ | customer | OTP + JWT (with session as fallback) |
| Backoffice | /api/v1/backoffice/ | employee/manager | Password + Session |

Django admin is disabled. All administrative operations are performed through the Backoffice API (decision D5).

### Features

- Online menu with category, product, and two-layer add-on structure
- Lucky Wheel on main dish products
- OTP with rate limits for customer login
- Frontend shopping cart (localStorage), order registration on the server
- Online payment via Zarinpal v4 with full idempotency
- Live order tracking (polling every 10–15 seconds)
- Live POS for the kitchen with receipt printing and alarm
- CRM (360° profile + internal notes + LTV)
- CMS (restaurant settings + section content + media with WebP)
- Manual refund flow by manager (paid → awaiting_refund → refunded)

## 2. Folder Structure

```text
fastfood-backend/
├── config/
│   ├── __init__.py            # exports celery_app
│   ├── settings.py            # the only settings file (D1 — no split);
│   │                          # DB_ENGINE selects SQLite (default) or PostgreSQL
│   ├── celery.py              # app + autodiscover
│   ├── urls.py                # health + schema + docs + mounts
│   ├── api_urls_storefront.py
│   ├── api_urls_backoffice.py
│   ├── wsgi.py / asgi.py
│   └── gunicorn.conf.py       # production config
│
├── common/                    # shared core
│   ├── models.py              # BaseModel, SoftDelete*
│   ├── exceptions.py          # BusinessException + 6 subclasses
│   ├── exception_handler.py   # error response envelope
│   ├── permissions.py         # IsStaffUser
│   ├── views.py               # BackofficeAPIView
│   ├── cache.py               # make_cache_key
│   ├── redis_client.py        # shared Redis client
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
├── docs/                      # project docs
├── requirements.txt
├── pytest.ini
├── manage.py
└── .env.example
```

### Structural Rules

Each app has three layers: models.py / selectors.py (read) / services.py (write).

The API layer is separated into apis/storefront/ and apis/backoffice/ — there is no business logic in views or serializers.

There is no Repository layer (D19).

## 3. Technology Stack and Key Decisions

| Layer | Technology |
| --- | --- |
| Framework | Django 5.x + DRF 3.15 |
| DB | PostgreSQL 16 (dev: SQLite) |
| Cache | Redis 7 |
| Async | Celery 5.4 + Beat (2 queues: high_priority and default) |
| JWT | djangorestframework-simplejwt (Storefront only) |
| Images | Pillow → WebP |
| Docs | drf-spectacular (separate Swagger per area) |
| Tests | pytest + pytest-django + Factory Boy |

Locked-in decisions (from D1–D25 + JWT)

| # | Decision | Result in code |
| --- | --- | --- |
| D1 | Money = integer toman | No Decimal anywhere |
| D2 | Timezone = Asia/Tehran, USE_TZ=True | daily_number_date based on timezone.localdate() |
| D3 | Custom user = accounts.Customer | AUTH_USER_MODEL = "accounts.Customer" |
| D4 | Backoffice = Session + is_staff | BackofficeAPIView uses SessionAuthentication only |
| D5 | Django admin disabled | django.contrib.admin not in INSTALLED_APPS |
| D6 | Soft delete in BaseModel | objects only sees alive rows |
| D7 | daily_number = Redis INCR | _assign_daily_number |
| D8 | OTP only in Redis, TTL 120s | apps/accounts/otp.py |
| D9 | Throttle: otp_request 5/h, otp_verify 10/h | throttle class in throttles.py, not in common/views.py |
| D10 | Delivery cost based on is_out_of_zone | _resolve_address + settings |
| D11 | customer cannot cancel a paid order | only manager can cancel |
| D12 | prep = max(items) + buffer | _compute_prep_time |
| D13 | Live POS polling + is_printed | get_live_orders + mark_order_printed |
| D14 | Zarinpal/sms.ir from env | settings.ZARINPAL_*, SMS_IR_* |
| D15 | Two Celery queues | CELERY_TASK_ROUTES |
| D16 | Error envelope | common/exception_handler.py |
| D17 | BaseModel fields | created_at, updated_at, deleted_at |
| D18 | 6 BusinessException subclasses | common/exceptions.py |
| D19 | No Repository layer | selectors + services only |
| D20 | No Variant model | different product sizes = separate records |
| D21 | Product status enum + is_main_dish | Product.Status, is_main_dish boolean |
| D22 | Two-layer AddOn | AddOn global + ProductAddOn per-product |
| D23 | SiteSection JSON | 6 valid keys |
| D24 | RestaurantSettings singleton | save() force pk=1 |
| D25 | WebP conversion | common/images.py (first Product.image, then MediaAsset.file) |

JWT: Storefront JWT + Session → Backoffice Session only

## 4. Quick Setup (Local)

### Prerequisites

- Python 3.12
- Redis 7 — optional for the default dev setup (`CACHE_BACKEND=locmem`); required for
  `CACHE_BACKEND=redis` or Celery workers

```powershell
# Redis via Docker
docker run -d --name fastfood-redis -p 6379:6379 redis:7-alpine

# or if installed directly
redis-server
```

### Installation

```powershell
cd backend
python -m venv venv
.env\Scriptsctivate
pip install -r requirements.txt
```

.env for dev (SQLite)

```dotenv
SECRET_KEY=dev-key-not-for-production
DEBUG=True
ALLOWED_HOSTS=127.0.0.1,localhost

# SQLite — no Postgres and no Redis server needed for the API to boot
DB_ENGINE=sqlite
# SQLITE_PATH=./db.sqlite3        # optional; defaults to BASE_DIR/db.sqlite3
CACHE_BACKEND=locmem              # use `redis` (with REDIS_URL) to mirror production

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

Database selection lives in `config/settings.py` (no separate settings module):

```python
DB_ENGINE = config("DB_ENGINE", default="sqlite")  # "sqlite" | "postgres"
```

With `DB_ENGINE=sqlite` (the default) Django uses `SQLITE_PATH` or
`BASE_DIR/db.sqlite3`. For PostgreSQL set `DB_ENGINE=postgres` plus the existing
`POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_HOST`,
`POSTGRES_PORT` variables; no code change is required. `CACHE_BACKEND=locmem`
(the default) uses Django's in-process cache, so Redis is optional in dev.

`CELERY_TASK_ALWAYS_EAGER` defaults to the value of `DEBUG`; in dev all Celery tasks
(OTP SMS, order, prep time change) run inline in the runserver process instead of the
Redis queue, so no worker or beat is needed.

### Startup

```powershell
python manage.py migrate
python manage.py create_staff 09123456789 "Test@1234" --superuser
python manage.py runserver
```

The server starts at http://127.0.0.1:8000. Check:

```bash
curl http://127.0.0.1:8000/health/
# {"success": true, "data": {"status": "ok"}}
```

Note: if typing `--settings` is annoying, create an alias in PowerShell:

```powershell
function devpy { python manage.py @args }
devpy migrate
devpy create_staff 09123456789 "Test@1234" --superuser
devpy runserver
```

## 5. Configuration and Environment Variables

| Variable | Required? | Default | Description |
| --- | --- | --- | --- |
| SECRET_KEY | ✅ in prod | dev-insecure | signing key for session, CSRF, JWT |
| DEBUG | — | True | set False in production (enables SSL/HSTS block) |
| ALLOWED_HOSTS | ✅ in prod | 127.0.0.1,localhost | comma-separated |
| DB_ENGINE | — | sqlite | `sqlite` (dev) or `postgres` |
| SQLITE_PATH | — | BASE_DIR/db.sqlite3 | SQLite file path |
| CACHE_BACKEND | — | locmem | `locmem` or `redis` |
| REDIS_URL | prod (redis cache) | redis://127.0.0.1:6379/0 | cache/Redis client |
| CELERY_BROKER_URL | ✅ | redis://.../1 | task queue |
| CELERY_RESULT_BACKEND | — | redis://.../2 | task results |
| MANAGER_PHONE | recommended | empty | for new order SMS |
| ZARINPAL_MERCHANT_ID | ✅ in prod | empty | — |
| ZARINPAL_CALLBACK_URL | ✅ in dev | must be HTTPS in prod | — |
| ZARINPAL_SANDBOX | — | True | False in prod |
| SMS_IR_API_KEY | recommended | empty | if empty, SMS is logged |
| SMS_IR_SENDER | recommended | empty | line number |
| PAYMENT_FRONTEND_RESULT_URL | recommended | dev URL | user redirects there after payment |
| JWT_ACCESS_LIFETIME_MINUTES | — | 60 | — |
| JWT_REFRESH_LIFETIME_DAYS | — | 7 | — |

In dev: if SMS_IR_API_KEY is empty, messages are logged to the runserver console. That means you read the OTP from the console — no real SMS is required.

## 6. Request Flow Architecture

### General Pattern

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

### Golden Rules

Views and serializers do validation and serialization only. No business logic.

All reads belong in selectors.py. No `Model.objects.filter(...)` in views.

All writes belong in services.py. No model instance is created or saved in views.

`@transaction.atomic` on every service that touches more than one table or performs a state transition.

`transaction.on_commit()` for external side effects (Celery tasks, cache invalidation).

### Error Envelope (D16)

Every non-2xx response:

```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE_STRING",
    "message": "user-facing Persian message",
    "details": null
  }
}
```

details can be null, a dict of field → message, or any other helper structure.

Successful responses return data directly (no wrapper).

## 7. Modules in Detail

### 7.1 Common

#### BaseModel + Soft Delete (D17)

```python
class BaseModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True, db_index=True)

    objects = SoftDeleteManager()   # only alive
    all_objects = models.Manager()  # all

    def soft_delete(self): ...      # deleted_at = now()
    def restore(self): ...           # deleted_at = None
    def hard_delete(self): ...       # real deletion
    def delete(self, ...): ...       # calls soft_delete()
```

Why: deletion is never physical so the audit trail is preserved. `objects` never returns deleted records.

SoftDeleteQuerySet:

- .alive() — only `deleted_at IS NULL`
- .dead() — only `deleted_at NOT NULL`
- .delete() — instead of deleting, `UPDATE deleted_at=now()`
- .hard_delete() — real deletion

#### Exceptions (D18)

```text
BusinessException (status 400)
├── NotFoundError            (404, NOT_FOUND)
├── PermissionDeniedError    (403, PERMISSION_DENIED)
├── ValidationError          (422, VALIDATION_ERROR)
├── RestaurantClosedError    (409, RESTAURANT_CLOSED)
├── OrderStateError          (409, INVALID_ORDER_STATE)
└── PaymentError             (402, PAYMENT_ERROR)
```

Any subclass in different apps may override `default_code`:

```python
class OTPExpiredError(ValidationError):
    default_code = "OTP_EXPIRED"
    status_code = 400
```

`custom_exception_handler`

```python
def custom_exception_handler(exc, context):
    if isinstance(exc, BusinessException):
        # uses its own code/message/status
    if isinstance(exc, DjangoValidationError):
        # → 422 with envelope
    response = drf_exception_handler(exc, context)
    if response:
        # DRF exception → wrap in envelope
    # default: 500 with generic message (no leak)
```

#### BackofficeAPIView

```python
class BackofficeAPIView(APIView):
    authentication_classes = [SessionAuthentication]  # not JWT
    permission_classes = [IsStaffUser]
```

Why separate: ensures JWT (which is only for Storefront) is not accepted on Backoffice. If an attacker has a customer token, they still cannot reach the backoffice unless they are staff and have a session.

#### common/cache.py

```python
CACHE_VERSION = "v1"
def make_cache_key(area: str, scope: str, version: str = CACHE_VERSION) -> str:
    return f"{area}:{scope}:{version}"
```

The cache backend uses `KEY_PREFIX="fastfood"`, so the final key becomes:

```text
fastfood:catalog:storefront_menu:v1
```

#### common/sms.py

```python
def send_sms(*, phone: str, message: str) -> bool
```

If `SMS_IR_API_KEY` is empty → it only logs and returns `True` (for dev).

Otherwise → `POST https://api.sms.ir/v1/send/bulk` with `x-api-key`.

On any error it returns `False` (without exception).

#### common/images.py

```python
def convert_image_to_webp(image_field, quality=85) -> ContentFile
def generate_webp_for_field(instance, source_field="image", target_field="webp_image")
```

If conversion fails → only a warning is logged and the original file remains. Best effort, not blocking.

### 7.2 Accounts

#### Customer model

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

Why it does not inherit from `BaseModel`: soft delete on users is problematic (auth is managed by `is_active`).

CustomerManager:

- `create_user(phone, password=None)` — if no password is supplied, `set_unusable_password()` is called (normal customer cannot log in with password).
- `create_superuser(phone, password)` — `is_staff=True` and `is_superuser=True`.

#### OTP (D8)

`apps/accounts/otp.py:`

```python
def generate_code() -> str:              # secrets.randbelow — cryptographic
def store_otp(*, phone, code) -> int:    # cache.set with TTL=120s
def get_otp_code(*, phone) -> str|None:
def delete_otp(*, phone) -> None:
```

Stored format: JSON `{"code": "123456"}` in key `fastfood:otp:code:0912...:v1`. Why JSON? To allow future metadata without changing type.

In verify:

```python
if not hmac.compare_digest(stored, code or ""):
    raise OTPInvalidError()
```

`compare_digest` prevents timing attacks.

Code consumption: after successful verification the code is deleted so it cannot be reused. If verification fails, the code remains until TTL expires.

#### Throttling (D9)

```python
class OTPRequestThrottle(SimpleRateThrottle):
    scope = "otp_request"  # 5/hour
    def get_cache_key(self, request, view):
        phone = request.data.get("phone")
        return f"{scope}:{phone}:{ip}"
```

Key = `phone:ip`. Meaning:

- one IP cannot request OTP for a single number more than 5 times per hour
- an attacker with IP rotation can bypass it → if you want a stronger limit, add a second throttle per phone (without IP)

`services.verify_otp` — complete

```python
def verify_otp(*, phone, code) -> Customer:
    normalized = normalize_phone(phone)
    stored = otp_service.get_otp_code(phone=normalized)
    if stored is None:
        raise OTPExpiredError()                  # code does not exist or TTL expired
    if not hmac.compare_digest(stored, code):
        raise OTPInvalidError()                  # wrong code, code not deleted
    otp_service.delete_otp(phone=normalized)     # consumed

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

#### Addresses

`CustomerAddress:`

- customer FK
- address_text
- recipient_name
- recipient_phone
- is_out_of_zone (determines delivery cost — D10)
- is_default (UniqueConstraint on `(customer)` with condition `is_default=True AND deleted_at IS NULL`)

Key point: before setting a new address to `is_default=True`, the service sets the old default to `False`:

```python
if data.get("is_default"):
    CustomerAddress.objects.filter(
        customer=customer, is_default=True
    ).update(is_default=False)
```

#### CustomerNote (CRM)

```python
class CustomerNote(BaseModel):
    customer = FK
    author = FK(Customer, null=True)  # employee who wrote it
    text = TextField
```

Notes are visible in the admin panel and printable on new order receipts (in a later phase; for now they are only stored).

#### Customer 360

`selectors.get_customer_360(customer_id):`

```python
{
    "customer": <Customer>,
    "addresses": [...],
    "notes": [...],
    "orders_count": int,
    "completed_orders_count": int,
    "lifetime_value": int,   # sum of total_amount of PAID orders
    "last_order_at": datetime|None,
}
```

Smart loop: it uses `django_apps.get_model("orders", "Order")` with try/except. If the `orders` app is not installed (during development), it returns zeros. At present it is installed, so it becomes real.

#### JWT

```python
def issue_tokens_for_customer(customer) -> {"access": str, "refresh": str}
def blacklist_refresh_token(refresh) -> bool  # True if successful
```

`OTPVerifyView` returns both session and JWT:

```python
login(request._request, customer)        # session cookie
token_pair = tokens.issue_tokens_for_customer(customer)  # JWT
return Response({"user": ..., "access": ..., "refresh": ...})
```

`TokenRefreshView` (`_SimpleJWTRefreshView`):

Input: `{"refresh": "..."}`

Output: `{"access": "...", "refresh": "..."}` — because rotation is enabled

Old refresh token is blacklisted.

Using the same old refresh token again → 401

`TokenLogoutView:`

Input: `{"refresh": "..."}`

Output: 204

It blacklists the refresh token and clears the session.

#### Staff Login

```python
def staff_login(phone, password):
    normalized = normalize_phone(phone)          # if invalid → InvalidCredentialsError (no leak)
    customer = Customer.objects.get(phone=normalized)
    if customer.is_blocked: raise AccountBlockedError()
    if not customer.is_active: raise AccountInactiveError()
    if not customer.is_staff: raise NotStaffError()
    if not customer.check_password(password): raise InvalidCredentialsError()
    customer.last_login = timezone.now()
    customer.save()
```

`POST /api/v1/backoffice/auth/login/` responds with `SessionAuthentication`:

```json
{
  "user": {"id": 1, "phone": "...", "is_staff": true, ...},
  "csrf_token": "..."
}
```

### 7.3 CMS

#### RestaurantSettings (singleton — D24)

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
        self.pk = 1  # force any save to pk=1
        super().save(*args, **kwargs)

    def is_open(self, now=None) -> bool:
        if self.is_temporarily_closed:
            return False
        if self.open_time < self.close_time:
            return self.open_time <= now < self.close_time  # same-day
        return now >= self.open_time or now < self.close_time  # overnight
```

Key point about `is_open`: closing time may be the next day relative to opening time. For example, 11:00 → 01:00 means from 11 AM to 1 AM. The algorithm:

If `open < close` → same day, between these two.

If `open >= close` → cross-midnight: from `open` to midnight, or from midnight to `close`.

Singleton via forced save: even if someone sets `instance.pk = 42` and saves it, it becomes `pk=1` again.

Seed: migration `0002_seed_restaurant_settings.py` creates the `pk=1` record on first migrate.

#### SiteSection (D23)

```python
class SiteSection(BaseModel):
    key = CharField(choices=[6 keys])
    content = JSONField(default=dict)
```

Allowed keys: `hero`, `header`, `footer`, `announcement`, `lucky_wheel`, `about_us`.

default content: `DEFAULT_SITE_SECTION_CONTENT` dict exists. If there is no record for a key, the selector uses the default — it never throws a "not found" error to the user.

UniqueConstraint: on `key` with `deleted_at IS NULL`. This means you can soft-delete a record and create a new one with the same key without conflict.

#### MediaAsset (D25)

```python
class MediaAsset(BaseModel):
    kind = CharField(choices=[("logo","Logo"),("banner","Banner"),("gallery","Gallery")])
    file = ImageField(upload_to="cms/%Y/%m/")
    webp_file = ImageField(upload_to="cms/webp/%Y/%m/", null=True, blank=True)
```

Upload: `services.create_media_asset:`

- saves the original file
- converts it to WebP with Pillow
- if conversion succeeds, saves the `webp_file`
- if it fails, only warns — the original file still works

Return URL:

```python
def get_image_url(obj):
    return obj.webp_file.url if obj.webp_file else (obj.file.url if obj.file else None)
```

#### Caching

`get_restaurant_settings():`

- key: `cms:restaurant_settings:v1`
- TTL: 1 hour
- invalidation: in `update_restaurant_settings` via `transaction.on_commit(lambda: cache.delete(...))`

`get_site_section(key):`

- key: `cms:site_section_<key>:v1`
- TTL: 1 hour
- invalidation: in `upsert_site_section`

Why `on_commit` instead of immediate deletion? If we delete the cache before the transaction commits and the transaction rolls back, the cache stays empty while the data is still old → the next request re-caches old data. With `on_commit`, cleanup only happens after a successful commit.

### 7.4 Catalog

#### Category

```python
class Category(BaseModel):
    name, slug, description, image, webp_image
    display_order, is_active
```

UniqueConstraint: on `slug` with `deleted_at IS NULL`. That means the slug can be reused after soft-delete.

Deletion: if a live product is linked to the category → `CategoryHasProductsError`. You must soft-delete the products first.

#### AddOn (D22 — first layer)

```python
class AddOn(BaseModel):
    name = CharField
    price = PositiveIntegerField
    is_available = BooleanField  # manager can disable globally
```

Scenario: the kitchen runs out of cheese → manager sets `is_available=False` → all products using this add-on lose it (in the menu and during new order creation).

#### Product (D21)

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

Three states (D21):

- AVAILABLE: visible in menu, purchasable, in Lucky Wheel
- OUT_OF_STOCK: visible in menu with disabled button, not in Lucky Wheel, cannot accept new orders
- HIDDEN: removed completely from menu and Lucky Wheel

No Variant (D20): “Margherita single” and “double” are two separate records with their own slug, price, image, and prep time.

`is_main_dish`:

- True → main dish, in Lucky Wheel
- False → appetizer/drink/add-on, in the shopping cart upsell suggestions (frontend)

#### ProductAddOn (D22 — second layer)

```python
class ProductAddOn(BaseModel):
    product = FK(Product)
    addon = FK(AddOn)
    min_quantity = PositiveSmallIntegerField(default=0)
    max_quantity = PositiveSmallIntegerField(default=5)
```

`CheckConstraint`: `min_quantity <= max_quantity` at DB level.

UniqueConstraint: on `(product, addon)` with `deleted_at IS NULL` — a product cannot have two links to the same add-on (but it can soft-delete the old one and create a new one).

In practice:

- AddOn “extra cheese” is created (`price=20k`, global)
- For “Margherita pizza”: `ProductAddOn(addon=cheese, min=0, max=3)`
- For “burger”: `ProductAddOn(addon=cheese, min=0, max=2)`

The customer may select up to 3 cheese pieces for pizza and up to 2 for burger.

#### Menu caching

`get_storefront_menu():`

- key: `catalog:storefront_menu:v1`
- TTL: 1 hour
- Query: categories → `prefetch_related(products excluding HIDDEN)` — only 2–3 queries

`OUT_OF_STOCK` is included (per spec), `HIDDEN` is not.

Response structure:

```json
{
  "categories": [
    {
      "id": 1, "name": "Pizza", "image_url": "...",
      "products": [
        {"id": 1, "name": "Margherita", "price": 150000,
         "status": "AVAILABLE", "is_main_dish": true, "image_url": "..."}
      ]
    }
  ]
}
```

Cache-safe: instead of pickling model instances, the selector builds a dict directly. Why? Because schema changes between deploys can make older pickles incompatible with the new code.

#### Lucky Wheel

`get_lucky_wheel_products(category_slug=None):`

Only `AVAILABLE + is_main_dish=True + category.is_active=True`

It may be filtered according to `?category=slug`

Separate cache (per category): `catalog:lucky_wheel:v1` and `catalog:lucky_wheel:pizzas:v1`

The spin logic is on the frontend. The backend only provides the list. The spec explicitly says not to create extra load.

#### Product detail (uncached)

`get_storefront_product(slug):`

- `select_related("category")`
- `prefetch_related(addon_links with select_related("addon"))`
- only `addon_links` where `addon.is_available=True` are returned

Response:

```json
{
  "id": 1, "name": "Margherita", "price": 150000,
  "category": {...}, "addons": [
    {"addon_id": 1, "name": "Extra cheese", "price": 20000,
     "min_quantity": 0, "max_quantity": 3}
  ]
}
```

### 7.5 Orders

#### State Machine (heart of the project)

```text
                          ┌──────────────────────┐
                          │  PENDING_PAYMENT     │  payment=UNPAID
                          │  (15 min timeout)    │
                          └──────────┬───────────┘
                    ┌────────────────┼────────────────┐
             successful payment    failed payment      15 minutes passed
                    ↓                ↓                 ↓
            ┌───────────────┐   (remains in PENDING)  CANCELED
            │  PROCESSING   │  payment=PAID
            │  daily_number │
            └───────┬───────┘
                    │ manager marks ready
                    ↓
            ┌───────────────┐
            │     READY     │  → SMS to customer
            └───────┬───────┘
                    │ manager marks completed
                    ↓
            ┌───────────────┐
            │   COMPLETED   │  (archive)
            └───────────────┘
```

Manager cancel (from any active stage except COMPLETED/CANCELED):

- PAID → CANCELED + payment=AWAITING_REFUND
- UNPAID → CANCELED + payment=UNPAID

Manager refund (from AWAITING_REFUND):

- → payment=REFUNDED (with `card_number` and `tracking_code` recorded)

#### Order model

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

delivery_address_snapshot: even if the address is later edited or soft-deleted, the invoice remains unchanged.

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

Why snapshot? If the manager changes pizza price tomorrow from 150k to 200k, yesterday's invoices must not change. Snapshot guarantees this.

#### Order creation (`services.create_order`)

```python
def create_order(*, customer, delivery_type, address_id, items, notes_to_kitchen=""):
    _ensure_restaurant_is_open()                        # RestaurantClosedError if closed
    # validated delivery_type
    address = _resolve_address(customer, address_id)    # NotFoundError if not owned by user
    # delivery_fee: PICKUP=0, DELIVERY with is_out_of_zone → in/out_zone_fee

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

`_build_order_items` validations:

- product must exist (`ProductNotFound`)
- product must not be `HIDDEN`
- product must be `AVAILABLE` (not `OUT_OF_STOCK`)
- product category must be `is_active=True`
- add-on must be defined for this product (`ProductAddOn`)
- add-on must have `addon.is_available=True`
- `0 <= addon.quantity <= link.max_quantity`
- if any fail → `ValidationError` with clear `details`.

#### Prep time (D12)

```python
def _compute_prep_time(items, product_by_id) -> int:
    max_prep = max(item.product.prep_time_minutes for item in items)
    buffer = RestaurantSettings.prep_time_buffer_minutes  # default 5
    return max_prep + buffer
```

Example: pizza 15 minutes, soda 0 minutes → max = 15, + buffer 5 = 20.

#### Daily number (D7)

`mark_order_paid` (called by `payments.verify_payment`):

```python
def _assign_daily_number(order):
    today = timezone.localdate()                    # based on Asia/Tehran
    key = f"order_seq:{today.isoformat()}"
    redis = get_redis()
    for attempt in range(10):
        number = int(redis.incr(key))
        if number == 1:
            redis.expire(key, 60*60*48)             # 48h TTL for cleanup
        order.daily_number = number
        order.daily_number_date = today
        try:
            order.save(update_fields=["daily_number", "daily_number_date", "updated_at"])
            return
        except IntegrityError:
            continue                                # collision → retry
    raise RuntimeError(...)
```

Why Redis `INCR`? Atomic, fast, lock-free. Why retry on `IntegrityError`? If Redis resets (dev or crash), numbers start at 1 again and may collide with previous records for the same day. The `UniqueConstraint((daily_number_date, daily_number))` catches the collision and retries.

`mark_order_paid` — full transaction

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

    _assign_daily_number(order)                     # inside the same transaction
    transaction.on_commit(lambda: send_order_registered_sms.delay(order.pk))
    return order
```

Note: SMS is sent only after commit — if the commit fails, SMS is not sent.

#### Live POS (D13)

`get_live_orders():`

```python
Order.objects.filter(status__in=[PROCESSING, READY]).order_by("expected_ready_at")
```

The frontend polls this every 10–15 seconds. Orders with `is_printed=False` trigger alarms and printing. After printing, the frontend calls `POST /orders/<id>/mark-printed/`.

#### Auto-cancel (D — 15 min)

```python
cancel_expired_unpaid_orders runs every 60 seconds via Celery Beat:
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

Why Beat instead of `apply_async(countdown=900)`? If the worker crashes, the countdown is lost and the order never gets canceled. Beat is idempotent and retries.

#### Prep time override

`update_prep_time(order_id, new_prep_time_minutes):`

Allowed only in PROCESSING or READY.

`expected_ready_at` is recalculated from `paid_at` (not `now()`).

`transaction.on_commit(send_prep_time_changed_sms.delay(...))`

Why use `paid_at`? If we use `now()`, the manager could delay ETA every time they change prep time. Using `paid_at` keeps the calculation anchored to the original payment time.

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
        # if code != 100 → ZarinpalRequestError

    def verify_payment(*, amount, authority) -> dict:
        # POST → {"data": {"code": 100 or 101, "ref_id": "..."}}
        # 100 = newly successful, 101 = already verified (idempotent)
        # any other code → ZarinpalVerifyError

    def build_redirect_url(authority) -> str:
        return f"{self.startpay_url}/{authority}"
```

urllib instead of requests: no extra dependency needed. Full control over timeout and exceptions.

#### Payment model

```python
class Payment(BaseModel):
    order = FK(Order, PROTECT)
    amount = PositiveIntegerField
    status = Enum: PENDING / SUCCEEDED / FAILED / CANCELED
    authority = CharField (unique per alive)
    ref_id = CharField (empty until verify)
    gateway_response_code, gateway_response_message
    verified_at, failed_at, canceled_at
```

UniqueConstraint on `authority` with `deleted_at IS NULL`: one authority at a time belongs to only one live Payment.

`start_payment_for_order`

```python
def start_payment_for_order(*, order):
    if order.status != PENDING_PAYMENT: raise OrderStateError()
    if order.payment_status != UNPAID: raise OrderStateError()
    if order.expires_at < now: raise OrderStateError("payment window expired")

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

#### verify_payment — idempotent (key!)

```python
@transaction.atomic
def verify_payment(*, authority, status):
    payment = Payment.objects.select_for_update().get(authority=authority)

    if payment.status == SUCCEEDED:
        return payment                    # idempotent: repeated callback
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

Why `select_for_update()`? If two callbacks arrive simultaneously (Zarinpal retries), the first acquires the lock, verifies, and commits. The second, after release, sees `payment.status == SUCCEEDED` and returns without a second verification → no double order transition.

Why `verify + mark_order_paid` in one `transaction.atomic`? If `mark_order_paid` fails (for example, `OrderStateError`), the `Payment` row also rolls back and remains `PENDING`. Then `reverify_pending_payments` retries later.

`code == 101`: Zarinpal returns this as “already verified”. We treat it as successful because `verify_data` includes `ref_id`.

#### Re-verify task (backup)

```python
reverify_pending_payments runs every 5 minutes:
```

```python
for payment in Payment.objects.filter(status=PENDING, created_at__lt=now-3min):
    try:
        verify_payment(authority=payment.authority, status="OK")
    except Exception:
        logger.warning(...)  # try again next round
```

Scenario: the user paid, but the callback did not arrive due to network or restart issues. This task re-verifies old `PENDING` payments older than 3 minutes. Since Zarinpal verification is idempotent, there is no risk.

#### Refund workflow (D11)

Manager `POST /orders/<id>/cancel/` → `cancel_order_by_manager`

- from PROCESSING/READY: `status=CANCELED`, `payment=AWAITING_REFUND`
- from PENDING: `status=CANCELED`, `payment=UNPAID`

Manager manually returns the money (card-to-card)

Manager `POST /orders/<id>/refund/` with `{card_number, tracking_code}` → `record_refund`

`payment=REFUNDED`, card and tracking code recorded.

## 8. Authentication and Authorization

### Full Table

| Endpoint | Auth | Permission | CSRF |
| --- | --- | --- | --- |
| POST /storefront/auth/otp/request/ | — | AllowAny | ✗ |
| POST /storefront/auth/otp/verify/ | — | AllowAny | ✗ |
| POST /storefront/auth/token/refresh/ | — | AllowAny | ✗ |
| POST /storefront/auth/token/logout/ | — | AllowAny | ✗ |
| POST /storefront/auth/logout/ | Session | IsAuthenticated | ✓ |
| GET /storefront/auth/me/ | JWT or Session | IsAuthenticated | — |
| POST /backoffice/auth/login/ | — | AllowAny | ✗ |
| POST /backoffice/auth/logout/ | Session | IsStaffUser | ✓ |
| all protected Backoffice endpoints | Session only | IsStaffUser | ✓ |

### Storefront Pattern

Frontend SPA → JWT:

```text
Authorization: Bearer <access>
```

(No CSRF required because the Authorization header itself is anti-CSRF.)

Traditional browser → Session:

```text
Cookie: sessionid=...
Header: X-CSRFToken: ...
```

Both work. `JWTAuthentication` is checked first; if no Authorization header exists, `SessionAuthentication` is used as fallback.

### Backoffice Pattern (why Session only — D4)

```python
class BackofficeAPIView(APIView):
    authentication_classes = [SessionAuthentication]
```

If an attacker has a customer JWT and the customer is also staff, the JWT still gets rejected because a session cookie is required. This is defense-in-depth.

Test: `test_jwt_rejected_on_backoffice` verifies this.

### CSRF — when is it required?

| Auth method | CSRF |
| --- | --- |
| JWT (Authorization header) | ✗ |
| Session (cookie) | ✓ for POST/PATCH/DELETE |

Why? CSRF attacks occur by auto-sending cookies. JWT sits in a manual header, so an attacker cannot send it from their own site.

## 9. Complete API Reference

### 9.1 Storefront

#### Auth

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

#### Catalog

| Method | Path | Auth | Params |
| --- | --- | --- | --- |
| GET | /catalog/menu/ | — | — |
| GET | /catalog/lucky-wheel/ | — | ?category=slug |
| GET | /catalog/products/ | — | `?q=&category=&category_id=&include_subcategories=&min_price=&max_price=&available=&in_stock=&discount=&is_main_dish=&sort=&limit=&offset=` (see `PROJECT_CONTEXT.md` §16) |
| GET | /catalog/suggestions/ | — | `?q=&limit=` (autocomplete, max 10 results, `did_you_mean` on typo) |
| GET | /catalog/products/<slug>/ | — | — |

#### Orders

| Method | Path | Auth | Body |
| --- | --- | --- | --- |
| GET | /orders/ | ✓ | — |
| POST | /orders/ | ✓ | {delivery_type, address_id?, notes_to_kitchen?, items: [{product_id, quantity, addons?: [{addon_id, quantity}]}]} |
| GET | /orders/<id>/ | ✓ | — |

#### Payments

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

#### Auth

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

#### Catalog

| Method | Path | Body |
| --- | --- | --- |
| GET/POST | /catalog/categories/ | {name, slug, parent_id?, description?, display_order?, is_active?} |
| GET/PATCH/DELETE | /catalog/categories/<id>/ | — (delete blocked when products or child categories exist) |
| POST | /catalog/categories/<id>/image/ | multipart image |
| GET/POST | /catalog/addons/ | {name, price, is_available?} |
| GET/PATCH/DELETE | /catalog/addons/<id>/ | — |
| GET/POST | /catalog/products/?category_id=&status=&is_main_dish=&search= | {name, slug, category_id, price, compare_at_price?, stock_quantity?, status?, is_main_dish?, prep_time_minutes?, display_order?, addons?} |
| GET/PATCH/DELETE | /catalog/products/<id>/ | — |
| POST | /catalog/products/<id>/image/ | multipart image |
| GET/PUT | /catalog/products/<id>/addons/ | {addons: [{addon_id, min_quantity, max_quantity}]} |

#### Orders

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

#### Payments

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
| GET | /api/v1/storefront/schema/ and /docs/ |
| GET | /api/v1/backoffice/schema/ and /docs/ (staff only) |

## 10. Troubleshooting

| Symptom | Cause | Solution |
| --- | --- | --- |
| no such table: accounts_customer | migration not run | `python manage.py migrate` |
| 500 on OTP request | Redis is down | `redis-cli ping` or `docker start fastfood-redis` |
| 403 CSRF Failed | X-CSRFToken header missing | `GET /auth/csrf/` and send the header |
| 401 Not authenticated | no session or JWT expired | request OTP again or refresh |
| 409 RestaurantClosedError | outside open hours | PATCH `restaurant-settings` to widen the hours |
| OTP not appearing in console | `SMS_IR_API_KEY` is set | clear it |
| NOT_STAFF on backoffice login | user `is_staff=False` | `python manage.py create_staff <phone> <pass> --superuser` |
| refresh not working | `token_blacklist` migration not run | `python manage.py migrate` |
| JWT rejected on backoffice | correct — by design | use session |
| `test_*.py` fail on Redis | DB 15 config but Redis down | bring Redis up |
| `billiard PermissionError` in Celery | default pool on Windows | `-P solo` or `-P threads` |
| Celery `Ctrl+C` does not work | Celery 5.4 bug | upgrade to `celery>=5.5` or use `-P solo` |
| migrate points to a different SQLite DB | two `db.sqlite3` files | `Get-ChildItem -Recurse -Filter db.sqlite3` |
| `daily_number` stays zero | successful payment not marked | check `Payment.verify_payment` |

## 11. Final Checklist

Goal: from zero to a fully working backend tested in ~30 minutes.

Prerequisite: `.env` according to section 4. Redis is only needed when `CACHE_BACKEND=redis` (or for Celery workers); the default SQLite + locmem setup boots without it.

### Step 0 — Setup

```powershell
python manage.py migrate
python manage.py create_staff 09123456789 "Test@1234" --superuser
python manage.py runserver
```

- [ ] migrate completed without errors
- [ ] create_staff printed `Created superuser user: 09123456789`
- [ ] runserver started at http://127.0.0.1:8000

### Step 1 — Health & Docs

```bash
curl http://127.0.0.1:8000/health/
```

- [ ] response: `{"success": true, "data": {"status": "ok"}}`
- [ ] browser: http://127.0.0.1:8000/api/v1/storefront/docs/ opens (list of endpoints)

### Step 2 — OTP Flow (customer)

```text
POST /api/v1/storefront/auth/otp/request/
Content-Type: application/json

{"phone": "09120000000"}
```

- [ ] response: `{"message": "کد تایید ارسال شد.", "expires_in": 120}`
- [ ] in the runserver console, the OTP code appears: `NNNNNN` — copy it

```text
POST /api/v1/storefront/auth/otp/verify/
Content-Type: application/json

{"phone": "09120000000", "code": "NNNNNN"}
```

- [ ] response includes `user`, `access`, and `refresh`

### Step 3 — Session Test

```text
GET /api/v1/storefront/auth/me/
```

- [ ] with a session cookie, response is `{"id": 1, "phone": "09120000000", ...}`

### Step 4 — JWT Test

- [ ] copy the `access` from step 2
- [ ] open a new Postman tab without cookies

```text
GET /api/v1/storefront/auth/me/
Authorization: Bearer <access>
```

- [ ] 200 response with the same user

### Step 5 — Refresh Test

```text
POST /api/v1/storefront/auth/token/refresh/
{"refresh": "<refresh from step 2>"}
```

- [ ] response includes a new `access` and `refresh`
- [ ] new refresh differs from the old one (rotation)
- [ ] use the old refresh again → 401

### Step 6 — Backoffice Login

```text
POST /api/v1/backoffice/auth/login/
{"phone": "09123456789", "password": "Test@1234"}
```

- [ ] 200 response with `user.is_staff: true` and `csrf_token`
- [ ] from this point, the customer JWT in a new tab does not work on backoffice:

```text
GET /api/v1/backoffice/orders/
Authorization: Bearer <customer access>
```

- [ ] response 401 or 403 (confirms D4)

### Step 7 — Create Category

```text
POST /api/v1/backoffice/catalog/categories/
X-CSRFToken: <csrf from login>
Content-Type: application/json

{"name": "Pizza", "slug": "pizzas", "display_order": 1}
```

- [ ] 201 with id: 1

### Step 8 — Create AddOn

```text
POST /api/v1/backoffice/catalog/addons/
X-CSRFToken: <csrf>

{"name": "Extra Cheese", "price": 20000}
```

- [ ] 201 with id: 1

### Step 9 — Create Product

```text
POST /api/v1/backoffice/catalog/products/
X-CSRFToken: <csrf>

{
  "name": "Margherita - Single",
  "slug": "margherita-single",
  "category_id": 1,
  "price": 150000,
  "is_main_dish": true,
  "prep_time_minutes": 15,
  "status": "AVAILABLE",
  "addons": [{"addon_id": 1, "min_quantity": 0, "max_quantity": 3}]
}
```

- [ ] 201 with id: 1 and addons: `[{"addon_id": 1, ...}]`

### Step 10 — Menu (public)

```text
GET /api/v1/storefront/catalog/menu/
```

- [ ] `categories[0].products[0].name == "Margherita - Single"`

### Step 11 — Lucky Wheel

```text
GET /api/v1/storefront/catalog/lucky-wheel/
```

- [ ] response includes Margherita

### Step 12 — Product Detail

```text
GET /api/v1/storefront/catalog/products/margherita-single/
```

- [ ] response includes `addons: [{"addon_id": 1, "name": "Extra Cheese", "price": 20000, "min_quantity": 0, "max_quantity": 3}]`

### Step 13 — Add Address (as customer)

Return to the customer tab (session or JWT):

```text
POST /api/v1/storefront/auth/addresses/
Authorization: Bearer <customer access>
Content-Type: application/json

{
  "address_text": "Tehran, Valiasr Street, No. 10",
  "recipient_name": "Ali Rezaei",
  "recipient_phone": "09120000000",
  "is_out_of_zone": false,
  "is_default": true
}
```

- [ ] 201

### Step 14 — Create Order

```text
POST /api/v1/storefront/orders/
Authorization: Bearer <access>

{
  "delivery_type": "PICKUP",
  "notes_to_kitchen": "no onion",
  "items": [
    {"product_id": 1, "quantity": 2, "addons": [{"addon_id": 1, "quantity": 1}]}
  ]
}
```

- [ ] 201 with:
  - status: `"PENDING_PAYMENT"`
  - payment_status: `"UNPAID"`
  - subtotal: `320000` (`150000*2 + 20000*1`)
  - total_amount: `320000`
  - prep_time_minutes: `20` (15 + 5 buffer)
  - expires_at roughly 15 minutes later
- [ ] save the id (example: 1)

### Step 15 — Payment Request (without a real Zarinpal)

Since `ZARINPAL_MERCHANT_ID` is empty, this endpoint returns an error. But the logic is tested. For a successful manual payment, use the shell:

```powershell
python manage.py shell -c "
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

- [ ] output: `status=PROCESSING, payment=PAID, daily=1`

### Step 16 — Order Tracking (customer)

```text
GET /api/v1/storefront/orders/1/
Authorization: Bearer <access>
```

- [ ] status: `"PROCESSING"`, `daily_number`: `1`, `expected_ready_at`: `<ISO datetime>`

### Step 17 — Live POS (admin)

Using the backoffice session:

```text
GET /api/v1/backoffice/orders/live/
Cookie: sessionid=<...>
```

- [ ] response is an array containing your order with `is_printed: false`
- [ ] ordered by `expected_ready_at`

### Step 18 — Mark Printed

```text
POST /api/v1/backoffice/orders/1/mark-printed/
X-CSRFToken: <csrf>
```

- [ ] `is_printed: true` and `printed_at` set

### Step 19 — Mark Ready (SMS to customer)

```text
POST /api/v1/backoffice/orders/1/mark-ready/
```

- [ ] status: `"READY"`
- [ ] in the runserver console, the SMS sending line appears (if `SMS_IR_API_KEY` is empty, it logs as a warning)

### Step 20 — Override Prep Time

```text
PATCH /api/v1/backoffice/orders/1/prep-time/
{"prep_time_minutes": 25}
```

- [ ] `prep_time_minutes: 25`, `expected_ready_at` recalculated (`paid_at + 25min`)

### Step 21 — Mark Completed

```text
POST /api/v1/backoffice/orders/1/mark-completed/
```

- [ ] status: `"COMPLETED"`

### Step 22 — Refund Flow (second order)

Create a second order (steps 14–15 with `order_id=2`):

- [ ] second order is `PROCESSING`

```text
POST /api/v1/backoffice/orders/2/cancel/
{"reason": "customer request"}
```

- [ ] status: `"CANCELED"`, payment_status: `"AWAITING_REFUND"`

```text
POST /api/v1/backoffice/orders/2/refund/
{"card_number": "6037-1234-5678-9012", "tracking_code": "123456789"}
```

- [ ] payment_status: `"REFUNDED"`, `refund_tracking_code`: `"123456789"`

### Step 23 — CRM

```text
GET /api/v1/backoffice/crm/customers/1/
```

- [ ] `orders_count: 2`, `lifetime_value: 320000` (only PAID orders count — the second order is REFUNDED, so lifetime_value may still be 320000 and `completed_orders_count: 1`)

```text
POST /api/v1/backoffice/crm/customers/1/notes/
{"text": "VIP customer"}
```

- [ ] 201 with `author_phone`

### Step 24 — CMS Settings

```text
PATCH /api/v1/backoffice/cms/restaurant-settings/
{"in_zone_delivery_fee": 60000, "prep_time_buffer_minutes": 7}
```

- [ ] 200 with new values

```text
GET /api/v1/storefront/cms/restaurant-status/
```

- [ ] `in_zone_delivery_fee: 60000`

### Step 25 — CMS Site Section

```text
PUT /api/v1/backoffice/cms/site-sections/hero/
{"content": {"title": "Hello", "subtitle": "Welcome"}}
```

- [ ] 200

```text
GET /api/v1/storefront/cms/site-sections/hero/
```

- [ ] `content.title == "Hello"`

### Step 26 — OTP Rate Limit

```text
POST /api/v1/storefront/auth/otp/request/  (× 6 rapid requests)
{"phone": "09129999999"}
```

- [ ] on the 6th request → 429 Too Many Requests with envelope `{"success": false, "error": {"code": "THROTTLED", ...}}`

### Step 27 — Authorization Isolation

Without login, call backoffice:

```text
GET /api/v1/backoffice/orders/
```

- [ ] 401 or 403

As a customer, try another customer's order:

```text
GET /api/v1/storefront/orders/999/
Authorization: Bearer <customer access>
```

- [ ] 404 `ORDER_NOT_FOUND`

### Step 28 — Run the Automated Tests

```powershell
pytest -v
```

- [ ] all tests PASS
- [ ] at least 40 tests (accounts, orders, payments, catalog, cms, jwt, permissions, n+1, e2e)

### Step 29 — Production Check

```powershell
$env:DEBUG="False"
python manage.py check --deploy
```

- [ ] System check identified no issues (0 silenced).
- [ ] if `SECRET_KEY` is dev, error `common.E001` appears → change it in `.env`

## Summary

If you complete all the steps above:

✅ The backend works completely — from OTP to payment, from Live POS to refund, CRM, and CMS.

### Remaining tasks for real production

- set production secrets and env
- deploy Redis and Celery workers with production config
- enable HTTPS and domains
- review rate limits and monitoring
- backup script and deploy pipeline
