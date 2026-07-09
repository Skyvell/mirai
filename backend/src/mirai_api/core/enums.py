from enum import StrEnum


class UploadStatus(StrEnum):
    """Parse lifecycle of a user-uploaded file, shared by all upload types."""

    UPLOADED = "uploaded"
    PARSED = "parsed"
    FAILED = "failed"
