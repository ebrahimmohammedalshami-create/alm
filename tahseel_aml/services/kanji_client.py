"""
Kanji / EFRM AML Screening and Transaction Monitoring Client
عميل الربط المباشر مع محرك فحص العقوبات ومراقبة المعاملات EFRM
مطابق تماماً لمواصفات الوثيقة الرسمية Requirements_UP_F.pdf
"""

import json
import logging
import uuid
from decimal import Decimal
from typing import Dict, Any, Optional
from django.utils import timezone
from ..interfaces import ISanctionsScreeningClient, ITransactionMonitoringClient
from ..models.choices import (
    ScreeningDecision, ScreeningRiskBand,
    TxnDecision, TxnMode, TxnChannel
)

logger = logging.getLogger(__name__)


class KanjiEFRMClient(ISanctionsScreeningClient, ITransactionMonitoringClient):
    """
    عميل الاتصال بمحرك Kanji EFRM / AML
    يدعم:
    1. فحص المنشآت الأساسية (Primary Entity Screening - KYB)
    2. فحص الأطراف والشركاء (Secondary Related Party Screening - KYC)
    3. فحص ومراقبة الحركات المالية (Transaction Monitoring - SYNC/ASYNC)
    """

    def __init__(
        self,
        screening_base_url: str = None,
        ruleengine_base_url: str = None,
        api_key: str = None,
        institution_id: str = None,
        source_system: str = None,
        is_sandbox: bool = None,
        timeout: int = None,
        base_url: str = None
    ):
        try:
            from django.conf import settings
            dj_screening = getattr(settings, 'AML_SCREENING_URL', "http://10.225.119.170:8000/screening/v1")
            dj_ruleengine = getattr(settings, 'AML_RULEENGINE_URL', "http://10.225.119.170:8083/ruleengine/v1")
            dj_api_key = getattr(settings, 'AML_API_KEY', "mock-api-key")
            dj_inst = getattr(settings, 'AML_INSTITUTION_ID', "ULTIMATE_PAY")
            dj_source = getattr(settings, 'AML_SOURCE_SYSTEM', "TAHSEEL")
            dj_sandbox = getattr(settings, 'AML_IS_SANDBOX', True)
            dj_timeout = getattr(settings, 'AML_TIMEOUT', 10)
        except Exception:
            dj_screening = "http://10.225.119.170:8000/screening/v1"
            dj_ruleengine = "http://10.225.119.170:8083/ruleengine/v1"
            dj_api_key = "mock-api-key"
            dj_inst = "ULTIMATE_PAY"
            dj_source = "TAHSEEL"
            dj_sandbox = True
            dj_timeout = 10

        self.screening_base_url = (base_url or screening_base_url or dj_screening).rstrip("/")
        self.ruleengine_base_url = (ruleengine_base_url or dj_ruleengine).rstrip("/")
        self.base_url = self.screening_base_url
        self.api_key = api_key if api_key is not None else dj_api_key
        self.institution_id = institution_id if institution_id is not None else dj_inst
        self.source_system = source_system if source_system is not None else dj_source
        self.is_sandbox = is_sandbox if is_sandbox is not None else dj_sandbox
        self.timeout = timeout if timeout is not None else dj_timeout

    # =========================================================================
    # 1. فحص الكيان التجاري (Primary Screening - Biller / Organization)
    # =========================================================================
    def screen_entity(
        self,
        entity_name: str = None,
        cr_number: str = None,
        biller=None,
        client_request_id: str = None
    ) -> Dict[str, Any]:
        """
        بناء وإرسال حمولة فحص الكيان التجاري (المنشأة المفوترة)
        متوافقة تماماً مع وثيقة المتطلبات و Swagger المباشر للسيرفر 10.225.119.170
        """
        req_id = client_request_id or f"TAH-SCR-{uuid.uuid4().hex[:12].upper()}"

        name = entity_name or (biller.name_en if biller else "") or (biller.name_ar if biller else "")
        cr = cr_number or (biller.commercial_register_number if biller else "")
        tax = (biller.tax_number if biller else "") or ""
        lic = (biller.license_number if biller else "") or ""
        country = (biller.country_code if biller else "YE") or "YE"
        address = (biller.street_address if biller else "") or ""
        phone = (biller.phone if biller else "") or ""
        email = (biller.email if biller else "") or ""
        ext_id = (biller.biller_code if biller else cr) or f"EXT-{uuid.uuid4().hex[:8]}"

        identifiers = []
        if cr:
            identifiers.append({"id_type": "REGISTRATION_ID", "id_value": cr})
        if tax:
            identifiers.append({"id_type": "TAX_ID", "id_value": tax})
        if lic:
            identifiers.append({"id_type": "OTHER", "id_value": lic})

        payload = {
            "entity_type": "ORGANIZATION",
            "entity_relation": "CUSTOMER",
            "external_entity_id": ext_id,
            "channel": "ONBOARDING",
            "source_system": self.source_system,
            "institution_id": self.institution_id,
            "client_request_id": req_id,
            "metadata": {
                "biller_code": ext_id,
                "submitted_by": "tahseel_onboarding_system"
            },
            "payload": {
                "name": name,
                "country": country,
                "address": address,
                "entity_sub_type": (biller.entity_sub_type if biller else "LIMITED_LIABILITY_COMPANY") or "LIMITED_LIABILITY_COMPANY",
                "channel": "ONBOARDING",
                "source_system": self.source_system,
                "external_entity_id": ext_id,
                "id_type1": "REGISTRATION_ID",
                "id_value1": cr,
                "id_type2": "TAX_ID",
                "id_value2": tax,
                "id_type3": "OTHER",
                "id_value3": lic,
                "identifiers": identifiers,
                "phone_no": phone,
                "email": email,
                "metadata": {
                    "biller_code": ext_id,
                    "submitted_by": "tahseel_onboarding_system"
                }
            }
        }

        if self.is_sandbox:
            return self._mock_entity_screening_response(payload)

        raw = self._send_http_request("/screening/entity/single", payload)
        return self._normalize_screening_response(raw, payload)

    # =========================================================================
    # 2. فحص الأفراد المرتبطين (Secondary Screening - Related Parties)
    # =========================================================================
    def screen_individual(
        self,
        name: str = None,
        id_number: str = None,
        party=None,
        client_request_id: str = None
    ) -> Dict[str, Any]:
        """
        بناء وإرسال حمولة فحص الأشخاص المرتبطين مع ربطهم بالكيان الأساسي
        (primary_entity_id) وفق الصفحات 3-5 من الوثيقة ومواصفات السيرفر
        """
        req_id = client_request_id or f"TAH-SCR-{uuid.uuid4().hex[:12].upper()}"

        full_name = name or (party.full_name_en if party else "") or (party.full_name_ar if party else "")
        id_val = id_number or (party.id_number if party else "")
        id_type = (party.id_type if party else "NATIONAL_ID") or "NATIONAL_ID"
        dob = party.date_of_birth.strftime("%Y-%m-%d") if (party and party.date_of_birth) else "1990-01-01"
        country = (party.country_code if party else "YE") or "YE"
        gender = (party.gender if party else "MALE") or "MALE"
        primary_entity_id = party.biller.biller_code if (party and party.biller) else "ORG-PRIMARY-001"
        relation_id = str(party.id) if party else f"REL-{uuid.uuid4().hex[:8]}"

        role_mapping = {
            'OWNER': 'CUSTOMER',
            'PARTNER': 'CUSTOMER',
            'AUTHORIZED_SIGNATORY': 'AUTHORIZED_SIGNATORY',
            'BOARD_MEMBER': 'DIRECTOR',
            'UBO': 'CUSTOMER'
        }
        relation = role_mapping.get(party.role if party else 'OWNER', 'DIRECTOR')

        identifiers = []
        if id_val:
            identifiers.append({"id_type": id_type, "id_value": id_val})

        payload = {
            "entity_type": "INDIVIDUAL",
            "entity_relation": relation,
            "external_entity_id": relation_id,
            "primary_entity_id": primary_entity_id,
            "relation_entity_id": relation_id,
            "channel": "ONBOARDING",
            "source_system": self.source_system,
            "institution_id": self.institution_id,
            "client_request_id": req_id,
            "metadata": {
                "role": party.role if party else "OWNER",
                "equity_percentage": float(party.equity_percentage) if party else 0.0,
                "is_pep": party.is_pep if party else False,
                "is_ubo": party.is_ubo if party else False
            },
            "payload": {
                "name": full_name,
                "dob": dob,
                "country": country,
                "gender": gender,
                "address": party.national_address if party else "",
                "channel": "ONBOARDING",
                "source_system": self.source_system,
                "external_entity_id": relation_id,
                "primary_entity_id": primary_entity_id,
                "id_type1": id_type,
                "id_value1": id_val,
                "identifiers": identifiers,
                "phone_no": party.phone if party else "",
                "email": party.email if party else "",
                "metadata": {
                    "role": party.role if party else "OWNER",
                    "equity_percentage": float(party.equity_percentage) if party else 0.0,
                    "is_pep": party.is_pep if party else False,
                    "is_ubo": party.is_ubo if party else False,
                    "pep_position": party.pep_position if party else ""
                }
            }
        }

        if self.is_sandbox:
            return self._mock_party_screening_response(payload)

        raw = self._send_http_request("/screening/entity/single", payload)
        return self._normalize_screening_response(raw, payload)

    # =========================================================================
    # 3. فحص الحركات المالية (Transaction Monitoring - SYNC / ASYNC)
    # =========================================================================
    def evaluate_transaction(self, txn_payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        إرسال معاملة مالية لمحرك EFRM لتقييم المخاطر لحظياً (SYNC) أو غير متزامن (ASYNC)
        مطابقة للمعايير المعتمدة في ultimate_pay_pg_card_txn_parameters.xlsx
        """
        payload = {
            "payload": {
                "institution_id": txn_payload.get("institution_id", self.institution_id),
                "source_system": txn_payload.get("source_system", "PG_SWITCH"),
                "fact": txn_payload.get("fact", "card_txn"),
                "mode": txn_payload.get("mode", TxnMode.SYNC),
                "channel": txn_payload.get("channel", TxnChannel.POS),
                "source_txn_id": txn_payload.get("source_txn_id", f"TXN-{uuid.uuid4().hex[:10]}"),
                "request_id": txn_payload.get("request_id", f"REQ-{uuid.uuid4().hex[:10]}"),
                "txnreqtrandate": txn_payload.get("txnreqtrandate", timezone.now().strftime("%y%m%d%H%M%S")),
                "pan": txn_payload.get("pan", "4111111111111111"),
                "processing_code": txn_payload.get("processing_code", "000000"),
                "amount": txn_payload.get("amount", 0),
                "stan": txn_payload.get("stan", "123456"),
                "local_time": txn_payload.get("local_time", timezone.now().strftime("%H%M%S")),
                "local_date": txn_payload.get("local_date", timezone.now().strftime("%m%d")),
                "mcc": txn_payload.get("mcc", "5411"),
                "country_code": txn_payload.get("country_code", "886"),
                "pos_entry_mode": txn_payload.get("pos_entry_mode", "051"),
                "pos_condition_code": txn_payload.get("pos_condition_code", "00"),
                "pin_capture_code": txn_payload.get("pin_capture_code", "12"),
                "acquiring_institution_id": txn_payload.get("acquiring_institution_id", "ACQ_ULTIMATE"),
                "forwarding_institution_id": txn_payload.get("forwarding_institution_id", "FWD_ULTIMATE"),
                "track2_data": txn_payload.get("track2_data", ""),
                "rrn": txn_payload.get("rrn", f"{uuid.uuid4().int % 1000000000000:012d}"),
                "authorization_id": txn_payload.get("authorization_id", "AUTH001"),
                "response_code": txn_payload.get("response_code", "00"),
                "terminal_id": txn_payload.get("terminal_id", "TERM001"),
                "customer_id": txn_payload.get("customer_id", "CUST000001"),
                "merchant_name_location": txn_payload.get("merchant_name_location", "TAHSEEL MERCHANT SANA'A YE"),
                "currency_code": txn_payload.get("currency_code", "886")
            }
        }

        if self.is_sandbox:
            return self._mock_transaction_response(payload)

        fact = txn_payload.get("fact", "card_txn")
        raw = self._send_http_request(f"/transaction/{fact}", payload, base_url=self.ruleengine_base_url)
        return self._normalize_transaction_response(raw, payload)

    # =========================================================================
    # محاكاة الاستجابات (Mock Engine / Sandbox Environment)
    # =========================================================================
    def _mock_entity_screening_response(self, request_payload: Dict[str, Any]) -> Dict[str, Any]:
        """محاكاة استجابة الفحص للكيان التجاري مطابقة لصفحة 6"""
        entity_name = request_payload["payload"]["name"].upper()
        # محاكاة حالة حظر عند احتواء الاسم على كلمات اشتباه
        is_hit = any(keyword in entity_name for keyword in ["TERROR", "DRUGS", "SANCTION", "BLOCKED"])

        decision = ScreeningDecision.CONFIRMED_MATCH if is_hit else ScreeningDecision.NO_MATCH
        risk_band = ScreeningRiskBand.CRITICAL if is_hit else ScreeningRiskBand.LOW
        score = 1000 if is_hit else 0

        matches = []
        if is_hit:
            matches.append({
                "match_id": 101,
                "list_source": "OFAC / CBY",
                "matched_name": entity_name,
                "match_score": 98.0,
                "risk_score": 1000,
                "risk_band": "CRITICAL",
                "match_type": "NAME",
                "matched_fields": {"name": True, "country": True}
            })

        return {
            "system": "Kanji EFRM / Watchlist Engine",
            "request_id": f"REQ-{uuid.uuid4().hex[:12]}",
            "client_request_id": request_payload["client_request_id"],
            "external_entity_id": request_payload["external_entity_id"],
            "decision": decision,
            "risk_band": risk_band,
            "overall_risk_score": score,
            "matched": is_hit,
            "hit_count": len(matches),
            "alert_generated": is_hit,
            "case_generated": is_hit,
            "case_id": f"CASE-{timezone.now().strftime('%Y%m%d')}-000001" if is_hit else None,
            "recommended_action": "HOLD_FOR_REVIEW" if is_hit else "ALLOW",
            "matched_lists": "OFAC, UN, CBY" if is_hit else "",
            "matches": matches,
            "score": Decimal('98.00') if is_hit else Decimal('0.00'),
            "raw_request": request_payload,
            "raw_response": {
                "status": "SUCCESS",
                "decision": "BLOCK" if is_hit else "ALLOW",
                "message": "Potential sanctions match found." if is_hit else "No matches found. Clear."
            }
        }

    def _mock_party_screening_response(self, request_payload: Dict[str, Any]) -> Dict[str, Any]:
        """محاكاة استجابة الفحص للشخص الطبيعي"""
        party_name = request_payload["payload"]["name"].upper()
        is_hit = any(keyword in party_name for keyword in ["TERROR", "CRIMINAL", "SANCTION"])

        decision = ScreeningDecision.CONFIRMED_MATCH if is_hit else ScreeningDecision.NO_MATCH
        risk_band = ScreeningRiskBand.CRITICAL if is_hit else ScreeningRiskBand.LOW
        score = 1000 if is_hit else 0

        return {
            "system": "Kanji EFRM / Watchlist Engine",
            "request_id": f"REQ-{uuid.uuid4().hex[:12]}",
            "client_request_id": request_payload["client_request_id"],
            "external_entity_id": request_payload["external_entity_id"],
            "primary_entity_id": request_payload["primary_entity_id"],
            "decision": decision,
            "risk_band": risk_band,
            "overall_risk_score": score,
            "matched": is_hit,
            "hit_count": 1 if is_hit else 0,
            "alert_generated": is_hit,
            "case_generated": is_hit,
            "case_id": f"CASE-{timezone.now().strftime('%Y%m%d')}-000002" if is_hit else None,
            "recommended_action": "HOLD_FOR_REVIEW" if is_hit else "ALLOW",
            "matched_lists": "OFAC Specially Designated Nationals" if is_hit else "",
            "score": Decimal('95.50') if is_hit else Decimal('0.00'),
            "raw_request": request_payload,
            "raw_response": {
                "decision": "BLOCK" if is_hit else "ALLOW",
                "message": "Screening completed successfully"
            }
        }

    def _mock_transaction_response(self, request_payload: Dict[str, Any]) -> Dict[str, Any]:
        """محاكاة استجابة تقييم الحركة المالية مطابقة لصفحات 12-13"""
        inner = request_payload["payload"]
        amount = Decimal(str(inner.get("amount", 0)))
        mode = inner.get("mode", TxnMode.SYNC)

        if mode == TxnMode.ASYNC:
            return {
                "request_id": inner["request_id"],
                "source_txn_id": inner["source_txn_id"],
                "institution_id": inner["institution_id"],
                "source_system": inner["source_system"],
                "fact": "card_txn",
                "mode": "ASYNC",
                "status": "ACCEPTED",
                "message": "Transaction received for asynchronous risk evaluation"
            }

        # فحص المعاملات ذات القيمة الكبيرة جداً كمثال لمخاطر عالية
        is_high_risk = amount >= Decimal('5000000')

        if is_high_risk:
            return {
                "request_id": inner["request_id"],
                "source_txn_id": inner["source_txn_id"],
                "institution_id": inner["institution_id"],
                "source_system": inner["source_system"],
                "fact": "card_txn",
                "mode": "SYNC",
                "channel": inner["channel"],
                "decision": TxnDecision.BLOCK,
                "risk_score": 850,
                "risk_severity": ScreeningRiskBand.CRITICAL,
                "policy_code": "POLICY_HIGH_VALUE_THRESHOLD",
                "matched_rule_count": 1,
                "alert_generated": True,
                "signals": [
                    {
                        "rule_code": "POS_HIGH_VALUE_TXN",
                        "signal_code": "POS_HIGH_VALUE_TXN",
                        "severity": "CRITICAL",
                        "score": 850,
                        "description": "High value POS transaction detected exceeding threshold"
                    }
                ],
                "message": "Transaction blocked due to high risk"
            }
        else:
            return {
                "request_id": inner["request_id"],
                "source_txn_id": inner["source_txn_id"],
                "institution_id": inner["institution_id"],
                "source_system": inner["source_system"],
                "fact": "card_txn",
                "mode": "SYNC",
                "channel": inner["channel"],
                "decision": TxnDecision.ALLOW,
                "risk_score": 120,
                "risk_severity": ScreeningRiskBand.LOW,
                "policy_code": "POLICY_DEFAULT",
                "matched_rule_count": 0,
                "alert_generated": False,
                "signals": [],
                "message": "Transaction allowed"
            }

    def _normalize_screening_response(self, raw: Dict[str, Any], request_payload: Dict[str, Any]) -> Dict[str, Any]:
        """تطبيع رد خادم RiskBrains EFRM الفعلي إلى نموذج قرارات تحصيل الداخلي"""
        dec_str = str(raw.get("decision", "CLEAR")).upper()
        if dec_str in ["CLEAR", "ALLOW", "NO_MATCH"]:
            decision = ScreeningDecision.NO_MATCH
        elif dec_str in ["ESCALATE", "BLOCK", "CONFIRMED_MATCH"]:
            decision = ScreeningDecision.CONFIRMED_MATCH
        else:
            decision = ScreeningDecision.POTENTIAL_MATCH

        band_str = str(raw.get("risk_band", "LOW")).upper()
        if band_str == "CRITICAL":
            risk_band = ScreeningRiskBand.CRITICAL
        elif band_str == "HIGH":
            risk_band = ScreeningRiskBand.HIGH
        elif band_str == "MEDIUM":
            risk_band = ScreeningRiskBand.MEDIUM
        else:
            risk_band = ScreeningRiskBand.LOW

        score = int(raw.get("overall_risk_score", 0))
        matched = decision != ScreeningDecision.NO_MATCH

        return {
            "system": "RiskBrains / Kanji EFRM Engine",
            "request_id": str(raw.get("request_id", "")),
            "client_request_id": request_payload.get("client_request_id"),
            "external_entity_id": request_payload.get("external_entity_id"),
            "decision": decision,
            "risk_band": risk_band,
            "overall_risk_score": score,
            "matched": matched,
            "hit_count": 1 if matched else 0,
            "alert_generated": matched,
            "case_generated": matched,
            "case_id": raw.get("case_id"),
            "recommended_action": "HOLD_FOR_REVIEW" if matched else "ALLOW",
            "matched_lists": raw.get("matched_lists", "RiskBrains Watchlist") if matched else "",
            "matches": raw.get("matches", []),
            "score": Decimal(str(score / 10.0)) if score else Decimal('0.00'),
            "raw_request": request_payload,
            "raw_response": raw
        }

    def _normalize_transaction_response(self, raw: Dict[str, Any], request_payload: Dict[str, Any]) -> Dict[str, Any]:
        """تطبيع استجابة محرك القواعد ومراقبة المعاملات RuleEngine (Port 8083)"""
        decision = raw.get("decision", TxnDecision.ALLOW)
        score = raw.get("totalScore", 0)
        severity = raw.get("highestSeverity", ScreeningRiskBand.LOW)
        matched_rules = raw.get("matchedRuleCount", 0)
        signals = raw.get("signals", [])
        alert_generated = raw.get("alertGenerated", False)
        policy_code = raw.get("policyCode", "")
        execution_id = raw.get("executionId")

        inner_payload = request_payload.get("payload", {})
        return {
            "fact": raw.get("fact", inner_payload.get("fact", "card_txn")),
            "source_txn_id": inner_payload.get("source_txn_id"),
            "request_id": inner_payload.get("request_id"),
            "institution_id": inner_payload.get("institution_id"),
            "source_system": inner_payload.get("source_system"),
            "decision": decision,
            "risk_score": score,
            "risk_severity": severity,
            "policy_code": policy_code,
            "matched_rule_count": matched_rules,
            "alert_generated": alert_generated,
            "signals": signals,
            "execution_id": execution_id,
            "raw_response": raw
        }

    def _send_http_request(self, endpoint: str, payload: Dict[str, Any], base_url: str = None) -> Dict[str, Any]:
        """إرسال الطلب الفعلي عبر شبكة HTTP إلى سيرفر RiskBrains EFRM / RuleEngine"""
        import urllib.request
        import urllib.error

        target_base = (base_url or self.screening_base_url).rstrip("/")
        url = f"{target_base}{endpoint}"
        headers = {
            "Content-Type": "application/json",
            "x-api-key": self.api_key,
            "X-API-KEY": self.api_key,
            "Authorization": f"Bearer {self.api_key}",
            "X-Source-System": self.source_system,
            "X-Institution-ID": self.institution_id
        }

        data_bytes = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(url, data=data_bytes, headers=headers, method="POST")

        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                res_body = resp.read().decode("utf-8")
                return json.loads(res_body)
        except urllib.error.HTTPError as e:
            err_body = e.read().decode("utf-8") if e.fp else ""
            logger.error(f"EFRM API HTTPError {e.code}: {err_body}")
            raise RuntimeError(f"EFRM API Error ({e.code}): {err_body}")
        except Exception as e:
            logger.error(f"EFRM API Connection Error: {str(e)}")
            raise RuntimeError(f"EFRM Connection failed: {str(e)}")

