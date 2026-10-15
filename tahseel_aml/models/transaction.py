"""
AML & EFRM Transaction Monitoring & Webhook Event Models
مطابق تماماً لمواصفات مراقبة المعاملات المالية الواردة في وثيقة Requirements_UP_F.pdf
"""

from decimal import Decimal
from django.db import models
from django.core.validators import MinValueValidator
from .base import ImmutableComplianceModel, TimeStampedUUIDModel
from .choices import TxnMode, TxnChannel, TxnDecision, ScreeningRiskBand
from .biller import Biller


class AMLTransactionMonitoringRecord(ImmutableComplianceModel):
    """
    سجل فحص المعاملات المالية ومكافحة الاحتيال (EFRM / Kanji Transaction Monitoring)
    غير قابل للتعديل للحفاظ على النزاهة القانونية والرقابية
    """
    biller = models.ForeignKey(
        Biller,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="monitored_transactions",
        verbose_name="المنشأة المفوترة"
    )

    # معاملات الربط بالنظام المزود
    institution_id = models.CharField(max_length=50, default="KANJI", verbose_name="رمز المؤسسة")
    source_system = models.CharField(max_length=50, default="CARD_TRANSACTION", verbose_name="النظام المصدر")
    fact = models.CharField(max_length=50, default="card_txn", verbose_name="نوع الحقيقة (Fact)")
    mode = models.CharField(max_length=10, choices=TxnMode.choices, default=TxnMode.SYNC, verbose_name="نمط الفحص")
    channel = models.CharField(max_length=10, choices=TxnChannel.choices, default=TxnChannel.POS, verbose_name="القناة")

    # معرفات الحركة
    source_txn_id = models.CharField(max_length=100, db_index=True, verbose_name="معرف الحركة لدى المصدر")
    request_id = models.CharField(max_length=100, db_index=True, verbose_name="معرف الطلب (Request ID)")
    rrn = models.CharField(max_length=50, blank=True, null=True, verbose_name="رقم المرجع (RRN)")
    stan = models.CharField(max_length=50, blank=True, null=True, verbose_name="رقم الأثر (STAN)")
    terminal_id = models.CharField(max_length=50, blank=True, null=True, verbose_name="رقم نقطة البيع / الجهاز")

    # بيانات البطاقة والمالية (مراعاة PCI-DSS بإخفاء البطاقة)
    pan_masked = models.CharField(max_length=30, verbose_name="رقم البطاقة المقنع (Masked PAN)")
    amount = models.DecimalField(
        max_digits=18,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name="مبلغ الحركة"
    )
    currency_code = models.CharField(max_length=10, default="356", verbose_name="رمز العملة")
    merchant_name_location = models.CharField(max_length=255, blank=True, null=True, verbose_name="اسم وموقع التاجر")
    customer_id = models.CharField(max_length=100, blank=True, null=True, verbose_name="معرف العميل")

    # نتائج تقييم المخاطر من محرك EFRM
    decision = models.CharField(
        max_length=20,
        choices=TxnDecision.choices,
        db_index=True,
        verbose_name="قرار المحرك"
    )
    risk_score = models.IntegerField(default=0, verbose_name="درجة الخطورة")
    risk_severity = models.CharField(
        max_length=20,
        choices=ScreeningRiskBand.choices,
        default=ScreeningRiskBand.LOW,
        verbose_name="شدة المخاطر"
    )
    policy_code = models.CharField(max_length=50, blank=True, null=True, verbose_name="كود السياسة")
    matched_rule_count = models.PositiveIntegerField(default=0, verbose_name="عدد القواعد المتطابقة")
    alert_generated = models.BooleanField(default=False, verbose_name="تم إنشاء تنبيه")
    signals = models.JSONField(default=list, blank=True, verbose_name="الإشارات والمؤشرات المكتشفة (Signals)")
    message = models.TextField(blank=True, null=True, verbose_name="رسالة الرد")

    raw_request_payload = models.JSONField(verbose_name="بيانات الطلب المرسلة")
    raw_response_payload = models.JSONField(verbose_name="بيانات الاستجابة المستلمة")

    class Meta:
        verbose_name = "سجل مراقبة حركة مالية (EFRM Txn Record)"
        verbose_name_plural = "سجلات مراقبة الحركات المالية (EFRM Txn Records)"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.source_txn_id} - {self.get_decision_display()} ({self.amount} {self.currency_code})"


class AMLWebhookEvent(TimeStampedUUIDModel):
    """
    سجل استقبال أحداث Webhook من نظام EFRM (القرارات غير المتزامنة وتحديثات القضايا)
    الصفحات 14-16 من وثيقة المتطلبات الرسمية
    """
    event_id = models.CharField(max_length=100, unique=True, db_index=True, verbose_name="معرف الحدث (Event ID)")
    event_type = models.CharField(
        max_length=50,
        db_index=True,
        verbose_name="نوع الحدث (TRANSACTION_DECISION / CASE_ACTION_UPDATE)"
    )
    event_time = models.DateTimeField(verbose_name="وقت الحدث")
    source_txn_id = models.CharField(max_length=100, db_index=True, verbose_name="معرف الحركة")
    case_id = models.CharField(max_length=100, blank=True, null=True, db_index=True, verbose_name="معرف القضية")
    case_status = models.CharField(max_length=50, blank=True, null=True, verbose_name="حالة القضية")
    final_action = models.CharField(max_length=50, blank=True, null=True, verbose_name="الإجراء النهائي")
    decision = models.CharField(max_length=20, blank=True, null=True, verbose_name="القرار")
    remarks = models.TextField(blank=True, null=True, verbose_name="ملاحظات المحلل")

    raw_payload = models.JSONField(verbose_name="حمولة الحدث الأصلية (Payload)")
    processed = models.BooleanField(default=False, verbose_name="تمت المعالجة في تحصيل")
    processed_at = models.DateTimeField(blank=True, null=True, verbose_name="تاريخ ووقت المعالجة")

    class Meta:
        verbose_name = "حدث Webhook رقابي (AML Webhook Event)"
        verbose_name_plural = "أحداث Webhook الرقابية (AML Webhook Events)"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.event_type} - {self.event_id} ({self.source_txn_id})"
