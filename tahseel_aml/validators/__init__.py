"""
Concrete Business Rule Validators (SRP & OCP)
كل مدقق مسؤول عن فحص محدد فقط دون تضارب
"""

from decimal import Decimal
from django.core.exceptions import ValidationError
from django.db.models import Sum
from django.utils import timezone
from ..interfaces import IBillerValidator, IPartyValidator
from ..models.biller import Biller
from ..models.party import BillerParty
from ..models.choices import BillerType, PartyRole, FATCAStatus


class GovernmentBillerValidator(IBillerValidator):
    """مدقق الكيانات الحكومية: يمنع الملاك ويفرض مفوضاً بالتوقيع"""
    def validate(self, biller: Biller) -> None:
        if biller.biller_type != BillerType.GOVERNMENT:
            return
        parties = biller.parties.all()
        if parties.filter(role__in=[PartyRole.OWNER, PartyRole.PARTNER]).exists():
            raise ValidationError("الجهات الحكومية لا تسجل ملاكاً أو شركاء، بل تسجل مفوضين بالتوقيع فقط.")
        if not parties.filter(role=PartyRole.AUTHORIZED_SIGNATORY).exists():
            raise ValidationError("الجهات الحكومية تتطلب وجود مفوض بالتوقيع معتمد واحد على الأقل.")


class MerchantBillerValidator(IBillerValidator):
    """مدقق المؤسسات الفردية (التاجر): مالك واحد بنسبة 100% ورخصة مهنية"""
    def validate(self, biller: Biller) -> None:
        if biller.biller_type != BillerType.MERCHANT:
            return
        if not biller.license_number:
            raise ValidationError("التاجر الفردي / المؤسسة الفردية يلزمها رقم ترخيص مزاولة المهنة.")
        owners = biller.parties.filter(role__in=[PartyRole.OWNER, PartyRole.PARTNER])
        if owners.count() != 1:
            raise ValidationError("المؤسسة الفردية (التاجر) يجب أن تحتوي على مالك واحد فقط.")
        owner = owners.first()
        if owner.equity_percentage != Decimal('100.00'):
            raise ValidationError(f"نسبة ملكية صاحب المؤسسة الفردية يجب أن تكون 100% (المسجل: {owner.equity_percentage}%).")


class PrivateCompanyBillerValidator(IBillerValidator):
    """مدقق الشركات الخاصة: سجل تجاري ومجموع حصص الشركاء = 100% بالضبط"""
    def validate(self, biller: Biller) -> None:
        if biller.biller_type != BillerType.PRIVATE_COMPANY:
            return
        if not biller.commercial_register_number:
            raise ValidationError("الشركات الخاصة تتطلب وجود رقم سجل تجاري معتمد.")
        # استخدام aggregate على مستوى قاعدة البيانات بدلاً من جلب السجلات للذاكرة (أداء أفضل)
        result = biller.parties.filter(
            role__in=[PartyRole.OWNER, PartyRole.PARTNER]
        ).aggregate(total=Sum('equity_percentage'))
        total_share = result['total'] or Decimal('0.00')
        if total_share != Decimal('100.00'):
            raise ValidationError(f"إجمالي نسب ملكية الشركاء في الشركة الخاصة يجب أن يساوي تماماً 100.00% (الحالي: {total_share}%).")


class MixedCompanyBillerValidator(IBillerValidator):
    """مدقق الكيانات المختلطة: حصة الشركاء أقل من 100% ومفوضون بالتوقيع"""
    def validate(self, biller: Biller) -> None:
        if biller.biller_type != BillerType.MIXED:
            return
        # استخدام aggregate على مستوى قاعدة البيانات بدلاً من جلب السجلات للذاكرة (أداء أفضل)
        result = biller.parties.filter(
            role__in=[PartyRole.OWNER, PartyRole.PARTNER]
        ).aggregate(total=Sum('equity_percentage'))
        total_share = result['total'] or Decimal('0.00')
        if total_share >= Decimal('100.00'):
            raise ValidationError(f"الكيان المختلط شراكة بين الدولة والقطاع الخاص، لذلك يجب أن تكون حصة الشركاء أقل من 100% (الحالي: {total_share}%).")
        if not biller.parties.filter(role=PartyRole.AUTHORIZED_SIGNATORY).exists():
            raise ValidationError("الكيان المختلط يتطلب وجود مفوضين بالتوقيع.")


class PartyComplianceValidator(IPartyValidator):
    """مدقق شروط الطرف الشخصية (العمر القانوني، الهوية، PEP، FATCA)"""
    def validate(self, party: BillerParty) -> None:
        today = timezone.now().date()
        if party.date_of_birth:
            if party.date_of_birth >= today:
                raise ValidationError("تاريخ الميلاد لا يمكن أن يكون في المستقبل.")
            age = (today - party.date_of_birth).days // 365
            if age < 18:
                raise ValidationError(f"عمر المالك/المفوض ({age} سنة) أقل من السن القانوني 18 سنة.")

        if party.id_expiry_date and party.id_expiry_date < today:
            raise ValidationError("الهوية منتهية الصلاحية. يجب تقديم وثيقة سارية.")

        if party.fatca_status in [FATCAStatus.US_PASSPORT, FATCAStatus.US_GREENCARD] and not party.us_tax_id:
            raise ValidationError("يجب إدخال الرقم الضريبي الأمريكي (SSN/TIN) لحاملي الجنسية أو البطاقة الخضراء الأمريكية.")

        if party.is_pep and not party.pep_position:
            raise ValidationError("يرجى تحديد المنصب السياسي للشخص المعرض سياسياً (PEP).")
