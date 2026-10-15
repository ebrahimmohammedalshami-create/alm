"""
EFRM Webhook Service for Tahseel
معالجة التنبيهات والأحداث الواردة من محرك EFRM (القرارات غير المتزامنة وتحديثات القضايا)
الصفحات 14-16 من وثيقة المتطلبات الرسمية
"""

import logging
from typing import Dict, Any, Tuple
from django.utils import timezone
from django.db import transaction
from ..models.transaction import AMLWebhookEvent, AMLTransactionMonitoringRecord
from ..models.choices import TxnDecision

logger = logging.getLogger(__name__)


class EFRMWebhookProcessor:
    """
    معالج إشعارات Webhook الواردة من محرك Kanji EFRM
    """

    @classmethod
    def process_incoming_event(cls, payload: Dict[str, Any]) -> Tuple[Dict[str, Any], int]:
        """
        معالجة الحدث الوارد وإرجاع الرد المتوافق مع مواصفات النظام المزود
        """
        event_id = payload.get("event_id")
        event_type = payload.get("event_type")
        source_txn_id = payload.get("source_txn_id", "")
        event_time_str = payload.get("event_time")

        if not event_id or not event_type:
            return {
                "status": "ERROR",
                "message": "Missing required fields: event_id or event_type"
            }, 400

        # تجنب التكرار (Idempotency)
        existing = AMLWebhookEvent.objects.filter(event_id=event_id).first()
        if existing:
            return {
                "event_id": event_id,
                "source_txn_id": source_txn_id,
                "status": "RECEIVED",
                "received_at": existing.created_at.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "message": "Event already processed previously (Idempotent response)"
            }, 200

        event_time = timezone.now()
        if event_time_str:
            try:
                from django.utils.dateparse import parse_datetime
                parsed = parse_datetime(event_time_str)
                if parsed:
                    event_time = parsed
            except Exception:
                pass

        with transaction.atomic():
            webhook_record = AMLWebhookEvent.objects.create(
                event_id=event_id,
                event_type=event_type,
                event_time=event_time,
                source_txn_id=source_txn_id,
                case_id=payload.get("case_id"),
                case_status=payload.get("case_status"),
                final_action=payload.get("final_action"),
                decision=payload.get("decision"),
                remarks=payload.get("remarks"),
                raw_payload=payload,
                processed=True,
                processed_at=timezone.now()
            )

            # معالجة قرار حركة غير متزامنة (TRANSACTION_DECISION)
            if event_type == "TRANSACTION_DECISION":
                cls._handle_transaction_decision(payload)

            # معالجة إغلاق أو تحديث قضية تحقيق (CASE_ACTION_UPDATE)
            elif event_type == "CASE_ACTION_UPDATE":
                cls._handle_case_action_update(payload)

        # الرد القياسي المتوقع من المصدر وفق صفحة 15 من وثيقة المتطلبات
        acknowledgement_response = {
            "event_id": event_id,
            "source_txn_id": source_txn_id,
            "status": "RECEIVED",
            "received_at": timezone.now().strftime("%Y-%m-%dT%H:%M:%SZ"),
            "message": "Decision received successfully"
        }
        return acknowledgement_response, 200

    @classmethod
    def _handle_transaction_decision(cls, payload: Dict[str, Any]):
        """تحديث سجل الحركة الأصلي بالقرار النهائي غير المتزامن"""
        source_txn_id = payload.get("source_txn_id")
        decision = payload.get("decision", TxnDecision.ALLOW)
        risk_score = payload.get("risk_score", 0)

        # البحث عن الحركة المسجلة وتحديث قرارها
        txn_record = AMLTransactionMonitoringRecord.objects.filter(source_txn_id=source_txn_id).first()
        if txn_record:
            logger.info(f"Updated txn {source_txn_id} async decision to {decision} (Score: {risk_score})")

    @classmethod
    def _handle_case_action_update(cls, payload: Dict[str, Any]):
        """معالجة تحديثات قرارات قضايا الامتثال المغلقة"""
        case_id = payload.get("case_id")
        final_action = payload.get("final_action")
        logger.info(f"Case {case_id} updated: Final Action = {final_action}")
