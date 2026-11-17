from __future__ import annotations

from django.core.checks import Error, register


@register()
def production_settings_check(app_configs, **kwargs):
    from django.conf import settings

    issues = []
    if not getattr(settings, "DEBUG", False):
        secret = getattr(settings, "SECRET_KEY", "") or ""
        if not secret or "dev" in secret.lower() or "insecure" in secret.lower():
            issues.append(
                Error(
                    "SECRET_KEY looks like a development default; set a "
                    "unique high-entropy value for production.",
                    id="common.E001",
                )
            )
        hosts = getattr(settings, "ALLOWED_HOSTS", [])
        if not hosts or "*" in hosts:
            issues.append(
                Error(
                    "ALLOWED_HOSTS must be an explicit list in production.",
                    id="common.E002",
                )
            )
    return issues