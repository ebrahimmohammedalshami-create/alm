"""
Django Views for Tahseel AML & EFRM Webhook Integration
مسؤولية الملف: استقبال ومعالجة طلبات Webhook الخارجية والتحقق الأمني
"""

import json
import logging
import hmac
import hashlib
from django.http import JsonResponse, HttpRequest, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST, require_GET
from django.conf import settings
from .services.webhook_service import EFRMWebhookProcessor

logger = logging.getLogger(__name__)


def _verify_webhook_signature(request: HttpRequest) -> bool:
    """
    التحقق من صحة توقيع الـ Webhook في حال تفعيل مفتاح التوقيع السري في الإعدادات
    """
    secret = getattr(settings, 'AML_WEBHOOK_SECRET', None)
    if not secret:
        # إذا لم يتم تحديد سر التوقيع في settings.py يتم تجاوز الفحص (اختياري)
        return True

    signature = request.headers.get('X-Signature') or request.headers.get('X-Webhook-Signature')
    if not signature:
        logger.warning("AML Webhook received without signature header.")
        return False

    computed = hmac.new(secret.encode('utf-8'), request.body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(signature, computed)


@csrf_exempt
@require_POST
def aml_webhook_view(request: HttpRequest) -> HttpResponse:
    """
    نقطة النهاية الرسمية لاستقبال إشعارات الـ Webhook من محرك EFRM
    الرابط: https://tahseeltest.ultimate-pay.net/api/aml/webhook/
    تدعم:
    1. TRANSACTION_DECISION: القرارات غير المتزامنة للحركات المالية (ASYNC)
    2. CASE_ACTION_UPDATE: تحديثات وإغلاق قضايا الامتثال
    """
    if not _verify_webhook_signature(request):
        return JsonResponse({
            "status": "ERROR",
            "message": "Invalid webhook signature"
        }, status=401)

    try:
        payload = json.loads(request.body.decode('utf-8'))
    except Exception as e:
        logger.error(f"AML Webhook JSON parsing error: {str(e)}")
        return JsonResponse({
            "status": "ERROR",
            "message": f"Malformed JSON: {str(e)}"
        }, status=400)

    try:
        response_data, status_code = EFRMWebhookProcessor.process_incoming_event(payload)
        return JsonResponse(response_data, status=status_code)
    except Exception as e:
        logger.exception(f"Unexpected error processing AML Webhook: {str(e)}")
        return JsonResponse({
            "status": "ERROR",
            "message": "Internal server error during webhook processing"
        }, status=500)


@require_GET
def aml_health_check_view(request: HttpRequest) -> HttpResponse:
    """
    فحص جاهزية وتوافر موديول الامتثال ومكافحة غسل الأموال
    """
    from django.utils import timezone
    return JsonResponse({
        "status": "HEALTHY",
        "service": "tahseel_aml",
        "timestamp": timezone.now().isoformat()
    }, status=200)
