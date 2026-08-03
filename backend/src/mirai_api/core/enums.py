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
