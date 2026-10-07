"""AIM - 날씨 기반 소비심리·수요 탄력도 모델 (docs/18)

비 오는 날값이 어떻게 바뀌는지를 규칙 단위로 표현한다. 두 축을 지킨다.

**축 1 — 근거 등급과 출처는 선택이 아니다.**
모든 규칙은 `evidence_tier`과 `source`을 가진다. 출처 없는 규칙은 이 모듈에
존재할 수 없다. 근거 없는 숫자로 매출을 약속한 것이 이 프로젝트가 반복해서
지켰던 유일한 규칙이기 때문이다.

**축 2 — 문헌 규칙은 이 매장의 규칙이 아니다.**
문헌에서 확인된 효과도 '다른 매장·다른 나라·다른 업종'의 결과다. 그래서 문헌
규칙은 등급 B에서 머문다. 이 매장의 POS 실측이 쌓이면 자동으로 A로 승격하고,
승격된 규칙이 서류 규칙을 **대체**한다.

Karpathy 원칙 2에 따라 성격(MBTI 등) 축은 **의도적으로 비워 둔다.**
근거 없는 성급한 분류를 코드에 넣지 않기 위해서이며, 근거가 쌓이면 추가한다.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from aim.schema import EvidenceTier, EnvironmentSignal, SalesLedgerFact

# --- 수요 축 정의 ---
# 성격(사람의 분류)이 아니라 **고매 행동**을 흔드는 축만 다룬다.
# 성격 축은 근거가 쌓일 때까지 비워 둔다(문서 18 §4).
AXIS_VISIT = "VISIT"          # 방문/유입
AXIS_BASKET = "BASKET"        # 장바구니 규모
AXIS_FREQUENCY = "FREQUENCY"  # 구매 빈도
AXIS_CATEGORY = "CATEGORY"    # 품목 구성 이동

DEMAND_AXES = (AXIS_VISIT, AXIS_BASKET, AXIS_FREQUENCY, AXIS_CATEGORY)

# --- 발생 조건 ---
COND_RAIN = "RAIN"          # 비 (강수확률 문턱 이상 또는 비/소나기 코드)
COND_SNOW = "SNOW"          # 눈
COND_COLD = "COLD"          # 기온 하강 (계절 기준 이하)
COND_HEAT = "HEAT"          # 폭염·고온
COND_CLEAR = "CLEAR"        # 맑음 + 일교차 큼

CONDITIONS = (COND_RAIN, COND_SNOW, COND_COLD, COND_HEAT, COND_CLEAR)


@dataclass(frozen=True)
class DemandRule:
    """문헌·관행에서 확인된 수요 변화 규칙 하나.

    frozen=True인 이유: 규칙은 근거와 함께 배포되는 산출물이다. 실행 중 값이
    바뀌면 그 규칙이 어느 연구에서 왔는지 더 이상 추적할 수 없다.
    """

    rule_id: str
    condition: str
    axis: str
    direction: int          # +1 증가, -1 감소
    magnitude: float        # 상대 변화율 추정치 (0.30 = 약 30%)
    mechanism: str          # 왜 그런가 (사람이 읽는 설명)
    source: str             # 출처. 빈 문자열 금지.
    source_kind: str        # 'LITERATURE' | 'STORE_MEASURED' | 'HEURISTIC'
    evidence_tier: EvidenceTier
    scope_note: str = ""    # 이 규칙이 성립하지 않는 조건
    confidence: float = 0.5  # 문헌 규칙은 낮게. 승격 시 올라간다.

    def __post_init__(self) -> None:
        if not self.source:
            raise ValueError(
                f"{self.rule_id}: 출처 없는 규칙은 배포할 수 없습니다 "
                "(docs/18 §2). 근거 없는 규칙이 매출 약속으로 이어집니다."
            )
        if self.axis not in DEMAND_AXES:
            raise ValueError(f"{self.rule_id}: 알 수 없는 수요 축 '{self.axis}'")
        if self.condition not in CONDITIONS:
            raise ValueError(f"{self.rule_id}: 알 수 없는 조건 '{self.condition}'")
        if self.direction not in (1, -1):
            raise ValueError(f"{self.rule_id}: direction은 +1 또는 -1이어야 합니다")
        if not 0.0 < self.magnitude <= 1.0:
            raise ValueError(f"{self.rule_id}: magnitude는 0~1 사이여야 합니다")


# --- 문헌 규칙 카탈로그 ---
#
# magnitude는 출처 논문의 효과 크기를 그대로 옮기지 않는다. 원 논문의 표본·
# 국가·업종이 우리 업종과 다르기 때문에, 이 값은 '방향을 잡기 위한 공칭치'다.
# 따라서 등급 B에서 머물고 금전적 약속에는 쓰이지 않는다(문서 18 §3.3).
LITERATURE_RULES: Tuple[DemandRule, ...] = (
    DemandRule(
        rule_id="RAIN_VISIT_DOWN",
        condition=COND_RAIN,
        axis=AXIS_VISIT,
        direction=-1,
        magnitude=0.20,
        mechanism="비가 오면 외출이 줄어 오프라인 방문이 줄어든다.",
        source="Parsons (2001) NZ 보행자 카운트; Aultman-Hall et al. (2009) 미국 쇼핑지구 보행량",
        source_kind="LITERATURE",
        evidence_tier=EvidenceTier.B_DERIVED,
        scope_note="한국 패션 유통에서는 강수 영향이 유의하지 않았다는 보고가 있다 "
                   "(Bahng & Kincade 2012). 음식점에는 적용되나 의류 소매에는 검증 전 적용 금지.",
        confidence=0.6,
    ),
    DemandRule(
        rule_id="RAIN_BASKET_UP",
        condition=COND_RAIN,
        axis=AXIS_BASKET,
        direction=1,
        magnitude=0.15,
        mechanism="출근 전에 한 번에 사 두는 '쌓아 사는' 행동. 방문은 줄어도 장바구니는 커진다.",
        source="Journal of Retailing (2021) The impact of weather on consumer behavior and retail performance",
        source_kind="LITERATURE",
        evidence_tier=EvidenceTier.B_DERIVED,
        scope_note="정기적으로 방문하는 매장에만 해당. 초회 매장에는 유의하지 않다.",
        confidence=0.55,
    ),
    DemandRule(
        rule_id="COLD_WARM_UP",
        condition=COND_COLD,
        axis=AXIS_CATEGORY,
        direction=1,
        magnitude=0.25,
        mechanism="기온이 떨어지면 따뜻한 음식·음료로 몸을 녹이는 수요가 늘어난다.",
        source="Bahng & Kincade (2012) 온도 편차와 한국 패션 유통 매출 (한국 데이터)",
        source_kind="LITERATURE",
        evidence_tier=EvidenceTier.B_DERIVED,
        confidence=0.65,
    ),
    DemandRule(
        rule_id="SNOW_COMFORT_UP",
        condition=COND_SNOW,
        axis=AXIS_CATEGORY,
        direction=1,
        magnitude=0.25,
        mechanism="적설 시 방한용·따뜻한 상품 수요 증가 (한국 유통에서 유의하게 측정됨).",
        source="Bahng & Kincade (2012) 한국 패션 유통: 적설은 유의한 요인",
        source_kind="LITERATURE",
        evidence_tier=EvidenceTier.B_DERIVED,
        confidence=0.65,
    ),
    DemandRule(
        rule_id="HEAT_FREQUENCY_DOWN",
        condition=COND_HEAT,
        axis=AXIS_FREQUENCY,
        direction=-1,
        magnitude=0.10,
        mechanism="기온이 오르면 외출 의지가 줄며 구매 건수가 감소한다.",
        source="Journal of Retailing (2021) 온도 상승 시 구매 품목 수 감소",
        source_kind="LITERATURE",
        evidence_tier=EvidenceTier.B_DERIVED,
        scope_note="냉방 시설이 완비된 매장에서는 영향이 반대일 수 있다.",
        confidence=0.5,
    ),
    DemandRule(
        rule_id="CLEAR_MOOD_UP",
        condition=COND_CLEAR,
        axis=AXIS_FREQUENCY,
        direction=1,
        magnitude=0.08,
        mechanism="햇빛 노출이 늘면 부정적 심리가 줄고 지출이 늘어난다.",
        source="Murray & Post (2010) 날씨와 소비자 정서 및 지출 행동",
        source_kind="LITERATURE",
        evidence_tier=EvidenceTier.B_DERIVED,
        confidence=0.45,
    ),
)


@dataclass
class DemandShift:
    """한 조건이 발동했을 때의 축별 이동량."""

    condition: str
    axis: str
    direction: int
    magnitude: float
    mechanism: str
    rule_ids: List[str] = field(default_factory=list)
    evidence_tier: EvidenceTier = EvidenceTier.C_ILLUSTRATIVE
    sources: List[str] = field(default_factory=list)
    promoted_from_evidence: bool = False

    @property
    def net_effect(self) -> float:
        """방향이 반영된 이동량. 양수면 증가."""
        return self.direction * self.magnitude

    def money_promise_allowed(self) -> bool:
        """이 이동량으로 금액을 약속할 수 있는가?

        C_ILLUSTRATIVE 는 어떤 상황에서도 금전적 약속으로 쓸 수 없다.
        B_DERIVED 는 카피 표현 근거까지만 허용한다.
        """
        return self.evidence_tier == EvidenceTier.A_MEASURED


class WeatherDemandModel:
    """기상 신호와 규칙 집합을 받아 수요 이동을 산출한다."""

    # 조건 판정 문턱값. 문헌 근거가 아니라 운영 판단이며 이름으로 고정한다.
    RAIN_PROB_THRESHOLD = 0.5
    COLD_TEMP_C = 10.0
    HEAT_TEMP_C = 30.0

    @classmethod
    def detect_conditions(cls, signal: EnvironmentSignal) -> List[str]:
        """신호에서 성립하는 조건들을 판정한다. 조건이 없으면 빈 목록."""
        found: List[str] = []

        code = str(signal.weather_code) if signal.weather_code is not None else ""
        label = cls._label_for(code, signal.weather_code_system)

        if signal.temp_c is not None and signal.temp_c >= cls.HEAT_TEMP_C:
            found.append(COND_HEAT)
        elif signal.temp_c is not None and signal.temp_c <= cls.COLD_TEMP_C:
            found.append(COND_COLD)

        prob = signal.precip_prob
        if prob is not None and prob >= cls.RAIN_PROB_THRESHOLD:
            found.append(COND_RAIN)

        if label:
            if "눈" in label:
                found.append(COND_SNOW)
            elif "소나기" in label or "비" in label or "이슬비" in label:
                if COND_RAIN not in found:
                    found.append(COND_RAIN)
            elif "맑음" in label:
                found.append(COND_CLEAR)

        # 중복 제거 + 결정론적 순서
        return [c for c in CONDITIONS if c in found]

    @classmethod
    def _label_for(cls, code: Optional[str], system: Optional[str]) -> Optional[str]:
        from aim.environment_sensor import EnvironmentSensor

        return EnvironmentSensor._weather_label(code, system)

    @classmethod
    def _prefer_measured(cls, rules: Tuple[DemandRule, ...]) -> Tuple[DemandRule, ...]:
        """같은 (조건, 축)에 실측 규칙이 있으면 문헌 규칙을 버린다.

        승격은 '문헌값과 이 매장의 실측값을 더하는 것'이 아니다. 이 매장의 숫자로
        말하는 것이지, 다른 매장의 숫자를 얹는 것이 아니다. 두 개를 합치면 근거가
        두 배가 아니라 **중복 계상**이 되어 버린다.
        """
        measured_keys = {
            (r.condition, r.axis) for r in rules if r.source_kind == "STORE_MEASURED"
        }
        if not measured_keys:
            return rules
        kept = [
            r
            for r in rules
            if r.source_kind == "STORE_MEASURED" or (r.condition, r.axis) not in measured_keys
        ]
        return tuple(kept)

    @classmethod
    def summarize(cls, shifts: List[DemandShift]) -> List[DemandShift]:
        """축 단위로 상쇄한 최종 판단.

        같은 축에 서로 반대 규칙이 걸릴 수 있다(폭염으로 구매 감소 + 맑음으로
        지출 증가). 이를 그대로 두면 사장님은 "10% 줄이세요, 8% 늘리세요"를
        동시에 받는다. 최종 판단은 반드시 축 단위 합계여야 한다.

        등급 처리는 **가장 보수적인 값**을 따른다. 한 축에 C 등급 규칙이 하나라도
        섞여 있으면 합계도 C다. 좋은 규칙이 나쁜 규칙을 씻어 올리는 것을 막는다.
        """
        by_axis: Dict[str, List[DemandShift]] = {}
        for shift in shifts:
            by_axis.setdefault(shift.axis, []).append(shift)

        summary: List[DemandShift] = []
        for axis, group in by_axis.items():
            net = sum(s.net_effect for s in group)
            direction = 1 if net >= 0 else -1
            tiers = [s.evidence_tier for s in group]
            worst = (
                EvidenceTier.C_ILLUSTRATIVE
                if EvidenceTier.C_ILLUSTRATIVE in tiers
                else EvidenceTier.B_DERIVED
                if EvidenceTier.B_DERIVED in tiers
                else EvidenceTier.A_MEASURED
            )
            summary.append(
                DemandShift(
                    condition="+".join(sorted({s.condition for s in group})),
                    axis=axis,
                    direction=direction,
                    magnitude=round(min(abs(net), 1.0), 4),
                    mechanism=" / ".join(s.mechanism for s in group),
                    rule_ids=[rid for s in group for rid in s.rule_ids],
                    evidence_tier=worst,
                    sources=sorted({src for s in group for src in s.sources}),
                    promoted_from_evidence=(
                        worst == EvidenceTier.A_MEASURED
                    ),
                )
            )
        return summary

    @classmethod
    def evaluate(
        cls,
        signal: EnvironmentSignal,
        rules: Optional[Tuple[DemandRule, ...]] = None,
        conditions: Optional[List[str]] = None,
    ) -> List[DemandShift]:
        """조건을 충족하는 규칙들을 축별로 모아 수요 이동을 만든다."""
        rules = rules if rules is not None else LITERATURE_RULES
        conditions = conditions if conditions is not None else cls.detect_conditions(signal)
        rules = cls._prefer_measured(rules)

        shifts: List[DemandShift] = []
        for condition in conditions:
            matched = [r for r in rules if r.condition == condition]
            if not matched:
                continue
            by_axis: Dict[str, List[DemandRule]] = {}
            for rule in matched:
                by_axis.setdefault(rule.axis, []).append(rule)

            for axis, group in by_axis.items():
                # 같은 축의 규칙은 합성한다. 서로 반대면 상쇄한다.
                net = sum(r.direction * r.magnitude for r in group)
                direction = 1 if net >= 0 else -1
                magnitude = round(min(abs(net), 1.0), 4)
                tiers = [r.evidence_tier for r in group]
                best = (
                    EvidenceTier.A_MEASURED
                    if EvidenceTier.A_MEASURED in tiers
                    else EvidenceTier.B_DERIVED
                    if EvidenceTier.B_DERIVED in tiers
                    else EvidenceTier.C_ILLUSTRATIVE
                )
                shifts.append(
                    DemandShift(
                        condition=condition,
                        axis=axis,
                        direction=direction,
                        magnitude=magnitude,
                        mechanism=" / ".join(r.mechanism for r in group),
                        rule_ids=[r.rule_id for r in group],
                        evidence_tier=best,
                        sources=sorted({r.source for r in group}),
                        promoted_from_evidence=best == EvidenceTier.A_MEASURED,
                    )
                )
        return shifts


class StoreElasticityProfile:
    """이 매장의 실측 날씨 탄력도.

    문헌 규칙을 대체한다. 서술이 아니라 이 매장의 숫자로 말하므로 A_MEASURED가
    가능하다. 단, **표본이 얕으면 승격하지 않는다.**
    """

    def __init__(
        self,
        store_id: str,
        min_samples_per_bucket: int = 5,
        samples_per_bucket: Optional[Dict[str, int]] = None,
        multipliers: Optional[Dict[str, Dict[str, float]]] = None,
    ) -> None:
        self.store_id = store_id
        self.min_samples_per_bucket = min_samples_per_bucket
        self.samples_per_bucket = samples_per_bucket or {}
        self.multipliers = multipliers or {}

    def bucket_has_enough_samples(self, bucket: str) -> bool:
        return self.samples_per_bucket.get(bucket, 0) >= self.min_samples_per_bucket

    def is_promoted(self, bucket: str) -> bool:
        return self.bucket_has_enough_samples(bucket) and bucket in self.multipliers

    def get_multiplier(self, bucket: str, axis: str) -> Optional[float]:
        if not self.is_promoted(bucket):
            return None
        return self.multipliers.get(bucket, {}).get(axis)

    def to_rules(self) -> Tuple[DemandRule, ...]:
        """실측 결과를 규칙으로 되돌린다. 승격 조건을 만족한 버킷만 포함."""
        rules: List[DemandRule] = []
        for bucket, axes in self.multipliers.items():
            if not self.is_promoted(bucket):
                continue
            for axis, multiplier in axes.items():
                direction = 1 if multiplier >= 1.0 else -1
                rules.append(
                    DemandRule(
                        rule_id=f"MEASURED_{bucket}_{axis}",
                        condition=bucket,
                        axis=axis,
                        direction=direction,
                        magnitude=round(abs(multiplier - 1.0), 4) or 0.01,
                        mechanism=f"이 매장 정산 데이터 실측 ({self.samples_per_bucket[bucket]}일 기준)",
                        source=f"SalesLedgerFact × 기상 {bucket} 버킷 (store_id={self.store_id})",
                        source_kind="STORE_MEASURED",
                        evidence_tier=EvidenceTier.A_MEASURED,
                        confidence=min(0.6 + 0.1 * self.samples_per_bucket[bucket], 0.95),
                    )
                )
        return tuple(rules)


class DemandCalibrator:
    """POS 정산 + 기상 기록으로 이 매장의 탄력도를 실측한다.

    데이터 저장은 하지 않는다. 호출자가 (정산사실, 조건) 쌍을 넘긴다.
    데이터베이스를 얹는 것은 이 스텝의 일이 아니다(문서 18 §6).
    """

    @classmethod
    def calibrate(
        cls,
        store_id: str,
        observations: List[Tuple[SalesLedgerFact, str]],
        min_samples_per_bucket: int = 5,
        baseline_condition: Optional[str] = None,
    ) -> StoreElasticityProfile:
        """observations: [(SalesLedgerFact, 조건 문자열), ...]

        버킷별 표본이 임계치 미만이면 그 버킷은 승격하지 않는다. 표본 2일치로
        '이 매장은 비 오는 날 2배가 판다'는 결론은 사실이 아니라 우연이다.

        기준선은 기본적으로 **가장 표본이 많은 버킷**(대개 맑은 날)이다. 전체
        평균을 쓰면 비교 대상 자신이 기준선에 섞여 크기가 부풀린다. 버킷이 하나뿐
        이면 자기 자신과의 비교가 되어 1.0이 나오는데, 그건 '아무 영향 없다'는
        뜻이 아니라 **비교할 기준이 없다**는 뜻이라 승격하지 않는다.
        """
        by_condition: Dict[str, List[SalesLedgerFact]] = {}
        for fact, condition in observations:
            by_condition.setdefault(condition, []).append(fact)

        if len(by_condition) < 2:
            # 비교 대상이 없다. 승격할 수 없다.
            return StoreElasticityProfile(
                store_id=store_id,
                min_samples_per_bucket=min_samples_per_bucket,
                samples_per_bucket={c: len(f) for c, f in by_condition.items()},
                multipliers={},
            )

        if baseline_condition is None:
            baseline_condition = max(by_condition, key=lambda c: len(by_condition[c]))
        baseline_facts = by_condition.get(baseline_condition) or []
        baseline = cls._averages(baseline_facts)

        multipliers: Dict[str, Dict[str, float]] = {}
        samples: Dict[str, int] = {}

        for condition, facts in by_condition.items():
            samples[condition] = len(facts)
            if condition == baseline_condition:
                continue  # 기준선 버킷은 자기 자신과 비교하지 않는다
            if len(facts) < min_samples_per_bucket:
                continue
            observed = cls._averages(facts)
            axes: Dict[str, float] = {}
            for axis in (AXIS_FREQUENCY, AXIS_BASKET, AXIS_VISIT):
                if baseline[axis]:
                    axes[axis] = round(observed[axis] / baseline[axis], 4)
            multipliers[condition] = axes

        return StoreElasticityProfile(
            store_id=store_id,
            min_samples_per_bucket=min_samples_per_bucket,
            samples_per_bucket=samples,
            multipliers=multipliers,
        )

    @staticmethod
    def _averages(facts: List[SalesLedgerFact]) -> Dict[str, float]:
        """버킷별 축 지표의 평균.

        AXIS_VISIT 은 **가동률**(1 - 유휴율)로 계산한다. 정산 기록이 가진 것은
        유휴율인데 유휴율이 높다는 것은 방문이 *적다*는 뜻이다. 유휴율을 그대로
        넣으면 부호가 뒤집혀 '비 오는 날 방문이 늘어난다'는 거꾸로 나간다.
        """
        if not facts:
            return {AXIS_FREQUENCY: 0.0, AXIS_BASKET: 0.0, AXIS_VISIT: 0.0}
        n = len(facts)
        return {
            AXIS_FREQUENCY: sum(f.transaction_count for f in facts) / n,
            AXIS_BASKET: sum(f.avg_ticket_krw for f in facts) / n,
            AXIS_VISIT: sum(1.0 - f.idle_capacity_rate for f in facts) / n,
        }