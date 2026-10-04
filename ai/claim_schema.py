from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, model_validator


class ClaimStatus(str, Enum):
    SUPPORTED = "supported"
    CONTRADICTED = "contradicted"
    UNCERTAIN = "uncertain"


class ExtractedClaim(BaseModel):
    """
    A factual claim extracted from the LLM response.

    The LLM provides the claim.
    Python validates the claim against business evidence.
    """

    entity: str = Field(
        description="Business entity such as a product or region."
    )

    metric: str = Field(
        description=(
            "Metric: revenue, return, return_rate, "
            "support_ticket, complaint, or refund."
        )
    )

    direction: Optional[str] = Field(
        default=None,
        description=(
            "Direction: increased, decreased, or unchanged."
        )
    )

    value: Optional[float] = Field(
        default=None,
        description="Numerical value mentioned in the claim."
    )

    unit: Optional[str] = Field(
        default=None,
        description=(
            "Unit such as percentage, percentage_points, "
            "or count."
        )
    )


class BusinessClaim(ExtractedClaim):
    """
    A claim after deterministic validation against business evidence.
    """

    status: ClaimStatus = Field(
        description=(
            "Validation result assigned by the Python validator."
        )
    )

    explanation: str = Field(
        description=(
            "Why the claim received its validation status."
        )
    )