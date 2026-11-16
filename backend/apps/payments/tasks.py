from __future__ import annotations

import logging

from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(name="apps.payments.tasks.reverify_pending_payments")
def reverify_pending_payments_task() -> int:
    from .services import reverify_pending_payments

    count = reverify_pending_payments()
    if count:
        logger.info("Re-verified %s pending payments.", count)
    return count