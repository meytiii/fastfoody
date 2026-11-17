from __future__ import annotations

from django.core.management.base import BaseCommand, CommandError

from apps.accounts.models import Customer


class Command(BaseCommand):
    help = "Create or update a staff user (is_staff=True)."

    def add_arguments(self, parser) -> None:
        parser.add_argument("phone", help="Staff phone number (e.g. 09120000000)")
        parser.add_argument("password", help="Initial password")
        parser.add_argument(
            "--superuser",
            action="store_true",
            help="Also set is_superuser=True.",
        )

    def handle(self, *args, **options) -> None:
        phone = (options["phone"] or "").strip()
        password = options["password"] or ""
        is_superuser = bool(options["superuser"])

        if not phone or not password:
            raise CommandError("Both phone and password are required.")

        customer, created = Customer.objects.get_or_create(phone=phone)
        customer.set_password(password)
        customer.is_staff = True
        customer.is_active = True
        if is_superuser:
            customer.is_superuser = True
        customer.save()

        status = "Created" if created else "Updated"
        role = "superuser" if is_superuser else "staff"
        self.stdout.write(
            self.style.SUCCESS(f"{status} {role} user: {customer.phone}")
        )