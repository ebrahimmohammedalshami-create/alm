"""
Interfaces for AML Services (DIP & ISP)
تطبيق مبدأ Dependency Inversion ومبدأ Interface Segregation

ملاحظة: نستخدم TYPE_CHECKING لتفادي الـ circular import
(models -> validators -> interfaces -> models)
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Dict, Any, TYPE_CHECKING

if TYPE_CHECKING:
    # هذا الاستيراد يحدث فقط عند فحص الأنواع (type hints) وليس عند التشغيل
    from ..models.biller import Biller
    from ..models.party import BillerParty


class IBillerValidator(ABC):
    """واجهة التحقق من صحة المفوتر وهيكل الشركاء (ISP)"""
    @abstractmethod
    def validate(self, biller: 'Biller') -> None:
        pass


class IPartyValidator(ABC):
    """واجهة التحقق من صحة الطرف المرتبط (عمر، هوية، PEP، FATCA) (ISP)"""
    @abstractmethod
    def validate(self, party: 'BillerParty') -> None:
        pass


class IRiskCalculationStrategy(ABC):
    """استراتيجية احتساب المخاطر (OCP & Strategy Pattern)"""
    @abstractmethod
    def calculate_score(self, biller: 'Biller') -> int:
        pass


class ISanctionsScreeningClient(ABC):
    """واجهة محرك فحص العقوبات وقوائم الحظر (DIP)"""
    @abstractmethod
    def screen_individual(
        self,
        name: str = None,
        id_number: str = None,
        party: 'BillerParty' = None,
        client_request_id: str = None
    ) -> Dict[str, Any]:
        pass

    @abstractmethod
    def screen_entity(
        self,
        entity_name: str = None,
        cr_number: str = None,
        biller: 'Biller' = None,
        client_request_id: str = None
    ) -> Dict[str, Any]:
        pass


class ITransactionMonitoringClient(ABC):
    """واجهة محرك فحص المعاملات المالية اللحظية EFRM (DIP)"""
    @abstractmethod
    def evaluate_transaction(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        pass


class IAuditLogger(ABC):
    """واجهة تسجيل التدقيق الرقابي (DIP)"""
    @abstractmethod
    def log_action(self, biller: 'Biller', action: str, user, previous_state=None, new_state=None, reason=None, ip_address=None) -> None:
        pass

