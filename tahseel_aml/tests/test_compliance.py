"""
Unit and Integration Tests for Tahseel AML & EFRM Compliance Module
اختبارات الوحدة والتكامل لموديول مكافحة غسل الأموال ومراقبة المعاملات
"""

import os
import unittest
from decimal import Decimal
from unittest.mock import MagicMock

# Configure standalone django settings if needed
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tahseel_aml.tests.mock_settings")

try:
    import django
    from django.conf import settings
    if not settings.configured:
        settings.configure(
            DEBUG=True,
            DATABASES={
                'default': {
                    'ENGINE': 'django.db.backends.sqlite3',
                    'NAME': ':memory:',
                }
            },
            INSTALLED_APPS=[
                'django.contrib.auth',
                'django.contrib.contenttypes',
                'tahseel_aml',
            ],
            USE_TZ=True,
        )
        django.setup()
        from django.core.management import call_command
        call_command('migrate', verbosity=0)
    DJANGO_AVAILABLE = True
except Exception as e:
    DJANGO_AVAILABLE = False
    django_error = str(e)


class TestKanjiEFRMClient(unittest.TestCase):
    """اختبارات عميل الربط مع محرك فحص العقوبات ومراقبة المعاملات"""

    def setUp(self):
        from tahseel_aml.services.kanji_client import KanjiEFRMClient
        self.client = KanjiEFRMClient(
            institution_id="ULTIMATE_PAY",
            source_system="TAHSEEL",
            is_sandbox=True
        )

    def test_default_institution_and_source_system(self):
        self.assertEqual(self.client.institution_id, "ULTIMATE_PAY")
        self.assertEqual(self.client.source_system, "TAHSEEL")
        self.assertTrue(self.client.is_sandbox)

    def test_screen_entity_clean_payload(self):
        res = self.client.screen_entity(
            entity_name="Al-Amal Telecom LLC",
            cr_number="CR-1002345"
        )
        self.assertEqual(res["decision"], "NO_MATCH")
        self.assertEqual(res["risk_band"], "LOW")
        self.assertFalse(res["matched"])
        self.assertEqual(res["overall_risk_score"], 0)

        # التحقق من حمولة الطلب المطابقة
        req = res["raw_request"]
        self.assertEqual(req["entity_type"], "ORGANIZATION")
        self.assertEqual(req["entity_relation"], "CUSTOMER")
        self.assertEqual(req["institution_id"], "ULTIMATE_PAY")
        self.assertEqual(req["source_system"], "TAHSEEL")
        self.assertEqual(req["payload"]["id_type1"], "REGISTRATION_ID")
        self.assertEqual(req["payload"]["id_value1"], "CR-1002345")
        self.assertTrue(len(req["payload"]["identifiers"]) >= 1)

    def test_screen_entity_sanctions_hit(self):
        res = self.client.screen_entity(
            entity_name="SANCTION BLOCKED TRADING",
            cr_number="CR-999999"
        )
        self.assertEqual(res["decision"], "CONFIRMED_MATCH")
        self.assertEqual(res["risk_band"], "CRITICAL")
        self.assertTrue(res["matched"])
        self.assertEqual(res["overall_risk_score"], 1000)
        self.assertTrue(res["alert_generated"])

    def test_screen_individual_clean_payload(self):
        res = self.client.screen_individual(
            name="Ahmed Al-Shami",
            id_number="01010098765"
        )
        self.assertEqual(res["decision"], "NO_MATCH")
        self.assertFalse(res["matched"])
        req = res["raw_request"]
        self.assertEqual(req["entity_type"], "INDIVIDUAL")
        self.assertEqual(req["institution_id"], "ULTIMATE_PAY")
        self.assertEqual(req["source_system"], "TAHSEEL")
        self.assertEqual(req["payload"]["id_type1"], "NATIONAL_ID")
        self.assertEqual(req["payload"]["id_value1"], "01010098765")

    def test_evaluate_transaction_sync_allow(self):
        txn_data = {
            "pan": "411111******1111",
            "amount": 25000.0,
            "channel": "POS",
            "mode": "SYNC",
            "source_txn_id": "TXN-TEST-001"
        }
        res = self.client.evaluate_transaction(txn_data)
        self.assertEqual(res["decision"], "ALLOW")
        self.assertEqual(res["institution_id"], "ULTIMATE_PAY")
        self.assertEqual(res["source_system"], "PG_SWITCH")
        self.assertEqual(res["fact"], "card_txn")
        self.assertFalse(res["alert_generated"])

    def test_evaluate_transaction_sync_block(self):
        txn_data = {
            "pan": "411111******1111",
            "amount": 10000000.0,  # قيمة تفوق 5 ملايين ريال
            "channel": "POS",
            "mode": "SYNC",
            "source_txn_id": "TXN-HIGH-002"
        }
        res = self.client.evaluate_transaction(txn_data)
        self.assertEqual(res["decision"], "BLOCK")
        self.assertEqual(res["risk_severity"], "CRITICAL")
        self.assertTrue(res["alert_generated"])

    def test_evaluate_transaction_async(self):
        txn_data = {
            "pan": "411111******1111",
            "amount": 50000.0,
            "mode": "ASYNC",
            "source_txn_id": "TXN-ASYNC-003"
        }
        res = self.client.evaluate_transaction(txn_data)
        self.assertEqual(res["status"], "ACCEPTED")
        self.assertEqual(res["mode"], "ASYNC")


from django.core.exceptions import ValidationError
from django.test import TestCase as DjangoTestCase

class TestComplianceORMModels(DjangoTestCase):
    """اختبارات نماذج البيانات وقواعد الأعمال في Django ORM"""

    def setUp(self):
        import uuid
        from tahseel_aml.models import Biller, BillerParty, BillerType, PartyRole
        from django.contrib.auth import get_user_model
        User = get_user_model()
        self.user, _ = User.objects.get_or_create(username="compliance_officer")

        self.biller = Biller.objects.create(
            biller_code=f"BIL-YE-{uuid.uuid4().hex[:6].upper()}",
            name_ar="شركة النور للتجارة",
            name_en="Al-Noor Trading LLC",
            biller_type=BillerType.PRIVATE_COMPANY,
            commercial_register_number="CR-887766",
            maker_user=self.user
        )

    def test_ubo_auto_calculation_threshold(self):
        from tahseel_aml.models import BillerParty, PartyRole
        # إضافة شريك بنسبة 30% -> يجب أن يصبح UBO تلقائياً (>= 25%)
        partner_major = BillerParty.objects.create(
            biller=self.biller,
            full_name_ar="علي محمد الشامي",
            full_name_en="Ali Mohamed Al-Shami",
            role=PartyRole.PARTNER,
            equity_percentage=Decimal('30.00'),
            id_number="0101998877",
            date_of_birth="1980-01-01"
        )
        self.assertTrue(partner_major.is_ubo, "شريك بحصة 30% يجب أن يتم وسمه كـ UBO تلقائياً")

        # إضافة شريك بنسبة 15% -> لا يعتبر UBO
        partner_minor = BillerParty.objects.create(
            biller=self.biller,
            full_name_ar="سامي أحمد حسن",
            full_name_en="Sami Ahmed Hassan",
            role=PartyRole.PARTNER,
            equity_percentage=Decimal('15.00'),
            id_number="0101998888",
            date_of_birth="1992-06-15"
        )
        self.assertFalse(partner_minor.is_ubo, "شريك بحصة 15% لا يجب أن يعتبر UBO")

    def test_immutable_compliance_record_cannot_be_deleted(self):
        from tahseel_aml.models import AMLAuditLog
        log = AMLAuditLog.objects.create(
            biller=self.biller,
            action_type="ONBOARDING_SCREENING_STARTED",
            performed_by=self.user
        )
        # محاولة الحذف يجب أن تثير خطأ ValidationError لحماية السجلات لمدة 10 سنوات
        with self.assertRaises(ValidationError):
            log.delete()

    def test_biller_risk_evaluation_service(self):
        from tahseel_aml.services import BillerComplianceService
        from tahseel_aml.models import BillerParty, PartyRole
        
        # إضافة شريك ذو منصب سياسي حساس PEP
        BillerParty.objects.create(
            biller=self.biller,
            full_name_ar="مسؤول رفيع",
            full_name_en="High Ranking Official",
            role=PartyRole.BOARD_MEMBER,
            equity_percentage=Decimal('10.00'),
            id_number="0101997766",
            date_of_birth="1975-03-20",
            is_pep=True,
            pep_position="وزير سابق"
        )

        service = BillerComplianceService()
        service.evaluate_and_update_risk(self.biller)
        self.biller.refresh_from_db()

        self.assertEqual(self.biller.risk_level, "HIGH")
        self.assertTrue(self.biller.requires_edd)

    def test_merchant_validator_rejects_multiple_partners(self):
        import uuid
        from tahseel_aml.models import Biller, BillerParty, BillerType, PartyRole
        from tahseel_aml.validators import MerchantBillerValidator

        merchant_biller = Biller.objects.create(
            biller_code=f"MERCH-{uuid.uuid4().hex[:6].upper()}",
            name_ar="مؤسسة التاجر الفردي",
            name_en="Sole Trader Est",
            biller_type=BillerType.MERCHANT,
            commercial_register_number="CR-MERCH-001",
            license_number="LIC-MERCH-888",
            maker_user=self.user
        )
        # إضافة مالك أول بنسبة 100%
        BillerParty.objects.create(
            biller=merchant_biller,
            full_name_ar="المالك الوحيد",
            full_name_en="Sole Owner",
            role=PartyRole.OWNER,
            equity_percentage=Decimal('100.00'),
            id_number="0101991122",
            date_of_birth="1982-04-10"
        )
        # التحقق يمر بنجاح
        MerchantBillerValidator().validate(merchant_biller)

        # محاولة إضافة شريك إضافي لتاجر فردي يجب أن ترفض
        BillerParty.objects.create(
            biller=merchant_biller,
            full_name_ar="شريك إضافي غير مسموح",
            full_name_en="Extra Partner Disallowed",
            role=PartyRole.PARTNER,
            equity_percentage=Decimal('20.00'),
            id_number="0101993344",
            date_of_birth="1988-08-20"
        )
        with self.assertRaises(ValidationError):
            MerchantBillerValidator().validate(merchant_biller)

    def test_webhook_processor_lifecycle_and_idempotency(self):
        from tahseel_aml.services import EFRMWebhookProcessor
        from tahseel_aml.models import AMLWebhookEvent

        event_payload = {
            "event_type": "TRANSACTION_DECISION",
            "event_id": "EVT-TEST-2026-9999",
            "event_time": "2026-10-15T14:30:10Z",
            "institution_id": "ULTIMATE_PAY",
            "source_system": "PG_SWITCH",
            "fact": "card_txn",
            "mode": "ASYNC",
            "source_txn_id": "TXN-TEST-9999",
            "decision": "BLOCK",
            "risk_score": 850,
            "case_id": "CASE-9999"
        }

        # المعالجة الأولى
        resp, status_code = EFRMWebhookProcessor.process_incoming_event(event_payload)
        self.assertEqual(status_code, 200)
        self.assertEqual(resp["status"], "RECEIVED")
        self.assertEqual(resp["event_id"], "EVT-TEST-2026-9999")
        self.assertTrue(AMLWebhookEvent.objects.filter(event_id="EVT-TEST-2026-9999").exists())

        # المعالجة الثانية لنفس الحدث (Idempotency) -> يجب أن يعيد 200 دون تكرار الحفظ
        resp2, status_code2 = EFRMWebhookProcessor.process_incoming_event(event_payload)
        self.assertEqual(status_code2, 200)
        self.assertIn("Idempotent", resp2["message"])
        self.assertEqual(AMLWebhookEvent.objects.filter(event_id="EVT-TEST-2026-9999").count(), 1)

    def test_webhook_http_view(self):
        import json
        from django.test import RequestFactory
        from tahseel_aml.views import aml_webhook_view, aml_health_check_view

        factory = RequestFactory()
        
        # Test Health Check
        health_req = factory.get('/api/aml/health/')
        health_resp = aml_health_check_view(health_req)
        self.assertEqual(health_resp.status_code, 200)
        self.assertIn(b"HEALTHY", health_resp.content)

        # Test Webhook HTTP View
        event_payload = {
            "event_type": "TRANSACTION_DECISION",
            "event_id": "EVT-VIEW-TEST-1111",
            "event_time": "2026-10-15T14:30:10Z",
            "institution_id": "ULTIMATE_PAY",
            "source_system": "PG_SWITCH",
            "fact": "card_txn",
            "mode": "ASYNC",
            "source_txn_id": "TXN-VIEW-1111",
            "decision": "BLOCK",
            "risk_score": 900
        }
        req = factory.post(
            '/api/aml/webhook/',
            data=json.dumps(event_payload),
            content_type='application/json'
        )
        resp = aml_webhook_view(req)
        self.assertEqual(resp.status_code, 200)
        resp_json = json.loads(resp.content.decode('utf-8'))
        self.assertEqual(resp_json["status"], "RECEIVED")
        self.assertEqual(resp_json["event_id"], "EVT-VIEW-TEST-1111")


if __name__ == '__main__':
    unittest.main()

