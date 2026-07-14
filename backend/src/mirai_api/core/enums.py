from enum import StrEnum


class UploadStatus(StrEnum):
    """Lifecycle of a user-uploaded file, from receipt to committed record.

    pending → processing → awaiting_review → committed is the happy path;
    failed is the terminal error branch from processing.
    """

    PENDING = "pending"
    PROCESSING = "processing"
    AWAITING_REVIEW = "awaiting_review"
    COMMITTED = "committed"
    FAILED = "failed"
