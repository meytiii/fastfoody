# Deployment Guide

## Prerequisites

- Python 3.12
- PostgreSQL 16
- Redis 7
- Gunicorn (already in `requirements.txt`)

## Environment

Copy `.env.example` to `.env` and set production values. Never commit `.env`.

Minimum production variables:

- `SECRET_KEY` — long random value
- `DEBUG=False`
- `ALLOWED_HOSTS` — comma-separated explicit domains
- `POSTGRES_*`
- `REDIS_URL`, `CELERY_BROKER_URL`, `CELERY_RESULT_BACKEND`
- `ZARINPAL_MERCHANT_ID`, `ZARINPAL_CALLBACK_URL` (public HTTPS)
- `SMS_IR_API_KEY`, `SMS_IR_SENDER`
- `MANAGER_PHONE`
- `PAYMENT_FRONTEND_RESULT_URL` (HTTPS)
- `SECURE_SSL_REDIRECT=True`, `SESSION_COOKIE_SECURE=True`, `CSRF_COOKIE_SECURE=True`

## Initial setup

```bash
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py create_staff <phone> <strong-password> --superuser
python manage.py check --deploy   # must return 0 issues