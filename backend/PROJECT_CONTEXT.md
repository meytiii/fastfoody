# PROJECT_CONTEXT

## 1. Project Overview

Django 5 REST API for a single-location fast-food restaurant. Two API surfaces: Storefront (`/api/v1/storefront/`) for customers and Backoffice (`/api/v1/backoffice/`) for staff. Includes catalog, orders with state machine, payments via Zarinpal, CMS, CRM, JWT/session auth, Celery background tasks.

## 2. Technology Stack

- Django 5.0.14, DRF 3.15, drf-spectacular
- Auth: custom `accounts.Customer` (AbstractBaseUser), SimpleJWT (rotation+blacklist), SessionAuthentication
- DB: SQLite default in `config/settings.py` (PostgreSQL config commented); Redis cache (DB 0 default)
- Celery 5.4 with Redis broker/results (DB 1/2), eager mode enabled
- Pillow for image/WebP conversion
- python-decouple for env
- Tests: pytest + pytest-django; Redis DB 15 in conftest

## 3. Project Structure

- `config/` settings, urls, celery, api url mounts
- `common/` BaseModel/soft delete, exceptions, handler, permissions, cache, redis, sms, images, checks
- `apps/accounts/` customers, addresses, notes, OTP, JWT, staff login
- `apps/catalog/` categories, products, addons, menu, lucky wheel
- `apps/cms/` restaurant settings singleton, site sections, media assets
- `apps/orders/` order state machine, items, snapshots, prep time, daily numbers
- `apps/payments/` Zarinpal client, payment verification, retries
- `tests/` pytest suite
- `docs/` design docs

## 4. Architecture

- Views/serializers validate only; reads in `selectors.py`, writes in `services.py`.
- `@transaction.atomic` for multi-table writes/state transitions; `transaction.on_commit` for side effects.
- Soft delete via `BaseModel`; default manager hides deleted.
- Unified error envelope via `common.exception_handler.custom_exception_handler`.
- Backoffice base `common.views.BackofficeAPIView` uses SessionAuthentication only (D4).

## 5. Important Modules

- `common/models.py`: SoftDeleteQuerySet/Manager, BaseModel
- `common/exceptions.py`: BusinessException hierarchy
- `common/cache.py`: `make_cache_key`
- `common/redis_client.py`: `get_redis` (lru_cached)
- `apps/accounts/services.py`: normalize_phone, OTP, addresses, CRM, staff_login
- `apps/accounts/selectors.py`: customer 360, order stats via dynamic model lookup
- `apps/orders/services.py`: create_order, mark_order_paid, transitions, cancel/refund, prep time
- `apps/orders/selectors.py`: order reads, live orders
- `apps/cms/services.py`: settings, site sections, media assets
- `apps/catalog/services.py` + selectors: menu cache, lucky wheel
- `apps/payments/services.py`: start/verify/retry/reverify

## 6. Database Schema

- `accounts.Customer` (AUTH_USER_MODEL), `CustomerAddress`, `CustomerNote`
- `catalog.Category`, `AddOn`, `Product`, `ProductAddOn`
- `cms.RestaurantSettings` (singleton pk=1, not soft-deletable), `SiteSection`, `MediaAsset`
- `orders.Order`, `OrderItem`, `OrderItemAddOn`
- `payments.Payment`
- Order snapshots store names/prices. Daily number unique per date. Soft delete on BaseModel tables.

## 7. API Architecture

- Storefront routes under `config/api_urls_storefront.py`; Backoffice under `config/api_urls_backoffice.py`.
- Public endpoints: OTP, catalog, CMS, payments callback.
- Auth: JWT Bearer or session; backoffice session only.
- Pagination LimitOffset, page size 20.

## 8. Critical Business Rules

- Restaurant must be open to create orders.
- Product must be AVAILABLE and category active; addons must be available and quantity within link limits.
- 15-minute payment timeout; auto-cancel via Celery Beat.
- Order transitions: PENDING_PAYMENT -> PROCESSING (on payment) -> READY -> COMPLETED; cancel rules and refunds.
- Prep time = max item prep + buffer; override anchors to paid_at.
- Daily number assigned atomically via Redis INCR with DB unique constraint retry.
- Payment verification idempotent with row lock.
- Snapshots preserve invoice history.

## 9. Workflows

- OTP request/verify -> get-or-create customer -> JWT+session.
- Create order -> validate -> create pending order -> payment request -> Zarinpal callback verify -> mark paid -> SMS.
- Manager POS: live orders, mark printed/ready/completed, cancel/refund, prep time override.
- Auto-cancel expired unpaid orders every 60s; reverify pending payments every 5m.

## 10. External Integrations

- Zarinpal v4 REST (urllib)
- sms.ir bulk SMS (logs if credentials empty)
- Redis cache + broker

## 11. Configuration

- `.env` / python-decouple; `REDIS_URL`, Celery URLs, Zarinpal, SMS, JWT lifetimes, manager phone.
- `TIME_ZONE=Asia/Tehran`, `LANGUAGE_CODE=fa-ir`.
- `CELERY_TASK_ALWAYS_EAGER=True`.
- `DEBUG` hardcoded True in `config/settings.py` (note).

## 12. Testing Status

- Ran `pytest`: 59 passed, 37 failed, 7 errors.
- Failures mainly: missing RestaurantSettings seed row for db-only tests; restaurant closed due to current time outside 11:00-01:00; soft delete `.dead()` on default manager; some payments errors cascade.
- Conftest uses Redis DB 15 and clears it.

## 13. Conventions

- snake_case services/selectors; no business logic in views.
- Persian user-facing messages.
- ` transaction.atomic` + `on_commit`.
- Soft delete instead of hard delete.
- Cache keys via `make_cache_key`; cache invalidation on commit.

## 14. Known Technical Debt / Risks

- README references `config.settings_sqlite` and seed migration `0002_seed_restaurant_settings`, neither present.
- `RestaurantSettings` has no seeded row after migrate; `get_restaurant_settings()` will raise DoesNotExist.
- `Category.objects.dead()` cannot see soft-deleted rows because default manager filters alive; tests expect it to.
- `DEBUG` hardcoded True in settings.
- `get_restaurant_settings()` caches model instance in Redis (pickle compatibility risk).
- `get_redis` lru_cached across settings changes in tests (conftest clears).
- Payments `start_payment_for_order` ignores IntegrityError duplicate authority and still returns URL.
- `reverify_pending_payments` counts only successful verifications; verify failures logged.
- No migration for seed data.

## 15. Unfinished / TODO

- Production settings profile, PostgreSQL enablement.
- Real Zarinpal credentials and HTTPS callback.
- Monitoring/backups/deploy pipeline documented as remaining.
