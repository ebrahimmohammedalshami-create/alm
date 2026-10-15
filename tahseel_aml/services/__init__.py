"""
AML Core Services (Strategy & Dependency Inversion)
خدمات احتساب المخاطر وتدقيق العمليات وفحص العقوبات
"""

from typing import List, Dict, Any, Optional
from decimal import Decimal
from django.utils import timezone
from ..interfaces import IRiskCalculationStrategy, ISanctionsScreeningClient, IAuditLogger, IBillerValidator
from ..models.biller import Biller
from ..models.choices import RiskLevel, ScreeningDecision
from ..models.screening import AMLAuditLog, AMLScreeningRecord
from ..validators import (
    GovernmentBillerValidator,
    MerchantBillerValidator,
    PrivateCompanyBillerValidator,
    MixedCompanyBillerValidator
)


class StandardRiskCalculationStrategy(IRiskCalculationStrategy):
    """استراتيجية احتساب المخاطر القياسية وفق قواعد البنك المركزي CBY (OCP)"""
    def calculate_score(self, biller: Biller) -> int:
        score = 30  # درجة الأساس

        # قطاعات ذات خطورة أعلى
        if biller.sector in ['CHARITY', 'FINANCIAL']:
            score += 25

        # وجود أشخاص معرضين سياسياً (PEP)
        if biller.parties.filter(is_pep=True).exists():
            score += 35

        # وجود اشتباه تطابق جزئي
        if biller.parties.filter(screening_decision=ScreeningDecision.POTENTIAL_MATCH).exists():
            score += 20

        return min(score, 100)


class BillerComplianceService:
    """
    خدمة التحقق الشامل وإدارة الامتثال للمفوترين (SRP & DIP)
    تعتمد على واجهات مجردة يمكن حقنها واختبارها بسهولة (Dependency Injection)
    """
    def __init__(
        self,
        risk_strategy: IRiskCalculationStrategy = None,
        screening_client: ISanctionsScreeningClient = None,
        validators: List[IBillerValidator] = None
    ):
        self.risk_strategy = risk_strategy or StandardRiskCalculationStrategy()
        self.screening_client = screening_client
        self.validators = validators or [
            GovernmentBillerValidator(),
            MerchantBillerValidator(),
            PrivateCompanyBillerValidator(),
            MixedCompanyBillerValidator(),
        ]

    def validate_biller_structure(self, biller: Biller) -> None:
        """تشغيل كافة المدققات المتوافقة مع نوع المنشأة"""
        for validator in self.validators:
            validator.validate(biller)

    def evaluate_and_update_risk(self, biller: Biller) -> None:
        """تقييم مخاطر الكيان وتحديد مستوى العناية الواجبة المشددة (EDD)"""
        # إذا كان هناك تطابق مؤكد مع قائمة عقوبات يُحظر الكيان فوراً
        if biller.parties.filter(screening_decision=ScreeningDecision.CONFIRMED_MATCH).exists():
            biller.risk_level = RiskLevel.PROHIBITED
            biller.risk_score = 100
            biller.requires_edd = True
            biller.risk_rationale = "حظر فوري: تطابق مؤكد مع قوائم العقوبات الصادرة (Confirmed Sanctions Match)."
            biller.save(update_fields=['risk_level', 'risk_score', 'requires_edd', 'risk_rationale'])
            return

        score = self.risk_strategy.calculate_score(biller)
        biller.risk_score = score
        has_pep = biller.parties.filter(is_pep=True).exists()

        if score >= 70 or has_pep:
            biller.risk_level = RiskLevel.HIGH
            biller.requires_edd = True
        elif score >= 40:
            biller.risk_level = RiskLevel.MEDIUM
            biller.requires_edd = False
        else:
            biller.risk_level = RiskLevel.LOW
            biller.requires_edd = False

        biller.last_risk_review_date = timezone.now().date()
        biller.save(update_fields=['risk_level', 'risk_score', 'requires_edd', 'last_risk_review_date'])

    def screen_biller_entity(self, biller: Biller, performed_by=None) -> Optional[AMLScreeningRecord]:
        """
        فحص الكيان التجاري نفسه (Primary Entity Screening - KYB) ضد قوائم العقوبات.
        مطابق تماماً لمواصفات الوثيقة الرسمية Requirements_UP_F.pdf
        """
        if not self.screening_client:
            return None

        result = self.screening_client.screen_entity(
            entity_name=biller.name_en or biller.name_ar,
            cr_number=biller.commercial_register_number,
            biller=biller
        )

        record = AMLScreeningRecord.objects.create(
            biller=biller,
            party=None,
            client_request_id=result.get('client_request_id'),
            provider_request_id=result.get('request_id'),
            searched_name=biller.name_en or biller.name_ar,
            searched_id_number=biller.commercial_register_number or biller.tax_number,
            screening_system=result.get('system', 'Kanji EFRM / Watchlist Engine'),
            decision=result.get('decision', ScreeningDecision.NO_MATCH),
            risk_band=result.get('risk_band', 'LOW'),
            overall_risk_score=result.get('overall_risk_score', 0),
            match_score=result.get('score', Decimal('0.00')),
            matched=result.get('matched', False),
            hit_count=result.get('hit_count', 0),
            matched_lists=result.get('matched_lists', ''),
            alert_generated=result.get('alert_generated', False),
            case_generated=result.get('case_generated', False),
            case_id=result.get('case_id'),
            recommended_action=result.get('recommended_action'),
            screened_at=timezone.now(),
            raw_request_payload=result.get('raw_request', {}),
            raw_response_payload=result.get('raw_response', result),
            reviewed_by=performed_by,
        )
        return record

    def screen_all_parties(self, biller: Biller, performed_by=None) -> List[AMLScreeningRecord]:
        """
        فحص جميع الأطراف الشخصيين (Secondary Related Party Screening - KYC)
        مع ربط كل طرف بالمنشأة الأساسية primary_entity_id
        """
        if not self.screening_client:
            return []

        records = []
        for party in biller.parties.all():
            result = self.screening_client.screen_individual(
                name=party.full_name_en or party.full_name_ar,
                id_number=party.id_number,
                party=party
            )
            record = AMLScreeningRecord.objects.create(
                biller=biller,
                party=party,
                client_request_id=result.get('client_request_id'),
                provider_request_id=result.get('request_id'),
                searched_name=party.full_name_en or party.full_name_ar,
                searched_id_number=party.id_number,
                screening_system=result.get('system', 'Kanji EFRM / Watchlist Engine'),
                decision=result.get('decision', ScreeningDecision.NO_MATCH),
                risk_band=result.get('risk_band', 'LOW'),
                overall_risk_score=result.get('overall_risk_score', 0),
                match_score=result.get('score', Decimal('0.00')),
                matched=result.get('matched', False),
                hit_count=result.get('hit_count', 0),
                matched_lists=result.get('matched_lists', ''),
                alert_generated=result.get('alert_generated', False),
                case_generated=result.get('case_generated', False),
                case_id=result.get('case_id'),
                recommended_action=result.get('recommended_action'),
                screened_at=timezone.now(),
                raw_request_payload=result.get('raw_request', {}),
                raw_response_payload=result.get('raw_response', result),
                reviewed_by=performed_by,
            )
            # تحديث حالة الفحص على الطرف
            party.screening_decision = result.get('decision', ScreeningDecision.NO_MATCH)
            party.last_screened_at = timezone.now()
            party.save(update_fields=['screening_decision', 'last_screened_at'])
            records.append(record)
        return records


class AuditService(IAuditLogger):
    """خدمة تسجيل وتوثيق العمليات الرقابية غير القابلة للتعديل (SRP)"""
    def log_action(
        self,
        biller: Biller,
        action: str,
        user,
        previous_state: Optional[Dict] = None,
        new_state: Optional[Dict] = None,
        reason: Optional[str] = None,
        ip_address: Optional[str] = None
    ) -> AMLAuditLog:
        return AMLAuditLog.objects.create(
            biller=biller,
            action_type=action,
            performed_by=user,
            ip_address=ip_address,
            previous_state=previous_state,
            new_state=new_state,
            change_reason=reason
        )


from .kanji_client import KanjiEFRMClient
from .webhook_service import EFRMWebhookProcessor

__all__ = [
    'StandardRiskCalculationStrategy',
    'BillerComplianceService',
    'AuditService',
    'KanjiEFRMClient',
    'EFRMWebhookProcessor',
]
