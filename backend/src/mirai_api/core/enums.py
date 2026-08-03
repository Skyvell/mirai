from enum import StrEnum


class UploadStatus(StrEnum):
    """Lifecycle of a user-uploaded file, from receipt to confirmed record.

    queued → processing → awaiting_review → confirmed is the happy path;
    failed is the terminal error branch from processing.
    """

    QUEUED = "queued"
    PROCESSING = "processing"
    AWAITING_REVIEW = "awaiting_review"
    CONFIRMED = "confirmed"
    FAILED = "failed"


class Sex(StrEnum):
    """Reference sex — the biological partition a lab stratifies its intervals by.

    Distinct from gender identity; a null column value means "any sex".
    """

    MALE = "male"
    FEMALE = "female"


class IntervalType(StrEnum):
    """Kind of biomarker interval: a population reference range or an optimal target."""

    REFERENCE = "reference"
    OPTIMAL = "optimal"
