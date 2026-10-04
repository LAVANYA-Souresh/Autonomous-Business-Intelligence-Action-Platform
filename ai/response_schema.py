from typing import List, Union

from pydantic import BaseModel, Field

from ai.claim_schema import ExtractedClaim


class BusinessAnalysis(BaseModel):

    summary: str = Field(
        description="Short summary of the business situation."
    )

    observed_facts: List[Union[str, ExtractedClaim]] = Field(
        default_factory=list,
        description=(
            "Facts directly supported by the available data. "
            "Each item may be plain text or a structured claim."
        )
    )

    supporting_evidence: List[Union[str, ExtractedClaim]] = Field(
        default_factory=list,
        description=(
            "Specific evidence supporting the analysis. "
            "Each item may be plain text or a structured claim."
        )
    )

    possible_explanations: List[str] = Field(
        default_factory=list,
        description=(
            "Possible explanations that are hypotheses, "
            "not confirmed causes."
        )
    )

    uncertainty: List[str] = Field(
        default_factory=list,
        description=(
            "Important limitations or unknowns."
        )
    )

    recommended_next_investigation: List[str] = Field(
        default_factory=list,
        description="Evidence-based next investigative steps."
    )

    claims: List[ExtractedClaim] = Field(
        default_factory=list,
        description=(
            "Structured factual claims extracted from the analysis. "
            "These claims will be independently validated against "
            "business evidence."
        )
    )