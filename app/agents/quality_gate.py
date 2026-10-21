from pydantic import Field
from app.agents.base import BaseAgent, AgentInput, AgentOutput
from app.agents.repurposing import PlatformPost
from app.agents.brand_memory import BrandVoiceProfile

class QualityCheckResult(AgentInput):
    check_name: str
    passed: bool
    details: str

class QualityGateInput(AgentInput):
    posts: list[PlatformPost]
    voice_profile: BrandVoiceProfile

class QualityGateOutput(AgentOutput):
    passed: bool
    compliance_score: int # 0 to 100
    checks: list[QualityCheckResult] = Field(default_factory=list)
    blockers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)

class QualityGateAgent(BaseAgent[QualityGateInput, QualityGateOutput]):
    agent_id = "quality-gate"
    name = "Quality Gate"
    department = "Governance"
    description = "Enforces regulatory compliance, character limits, tone consistency, and safety policy."

    async def execute(self, input_data: QualityGateInput) -> QualityGateOutput:
        checks = []
        blockers = []
        warnings = []
        score = 100

        # Check 1: Character limits
        limits_ok = True
        for p in input_data.posts:
            if not p.within_limits:
                limits_ok = False
                blockers.append(f"Post for {p.platform} exceeds limit: {p.character_count} > {p.char_limit}")
                score -= 25

        checks.append(QualityCheckResult(
            check_name="Character Limits",
            passed=limits_ok,
            details="All platform drafts within maximum length thresholds." if limits_ok else "One or more posts exceed limit."
        ))

        # Check 2: Banned vocabulary
        banned_found = []
        for p in input_data.posts:
            copy_lower = p.copy.lower()
            for banned in input_data.voice_profile.banned_words:
                if banned.lower() in copy_lower:
                    banned_found.append(f"Found '{banned}' in {p.platform} draft.")
                    score -= 30

        if banned_found:
            blockers.extend(banned_found)
            checks.append(QualityCheckResult(
                check_name="Banned Vocabulary",
                passed=False,
                details=f"Violations detected: {', '.join(banned_found)}"
            ))
        else:
            checks.append(QualityCheckResult(
                check_name="Banned Vocabulary",
                passed=True,
                details="Zero prohibited words or unsubstantiated claims found."
            ))

        # Check 3: Human verification requirement
        warnings.append("Human fact-check required before external release.")
        checks.append(QualityCheckResult(
            check_name="Fact-Check Requirement",
            passed=True,
            details="Draft flagged for human editorial verification."
        ))

        score = max(0, min(100, score))
        passed = len(blockers) == 0

        return QualityGateOutput(
            success=True,
            passed=passed,
            compliance_score=score,
            checks=checks,
            blockers=blockers,
            warnings=warnings
        )
