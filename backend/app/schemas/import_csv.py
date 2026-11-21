from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import ImportStatus, ImportType


class RowValidationError(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    row: int
    field: str
    value: Any
    errorCode: str
    message: str
    suggestion: str


class ImportPreviewResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    batchId: str = Field(alias="batch_id")
    importType: ImportType = Field(alias="import_type")
    cycleId: str | None = Field(default=None, alias="cycle_id")
    fileName: str = Field(alias="file_name")
    totalRows: int = Field(alias="total_rows")
    validRows: int = Field(alias="valid_rows")
    invalidRows: int = Field(alias="invalid_rows")
    duplicateCount: int = Field(default=0, alias="duplicate_count")
    unknownReferenceCount: int = Field(default=0, alias="unknown_reference_count")
    alreadyImported: bool = Field(default=False, alias="already_imported")
    warningMessage: str | None = Field(default=None, alias="warning_message")
    errors: list[RowValidationError] = Field(default_factory=list)
    sampleValidRows: list[dict[str, Any]] = Field(default_factory=list, alias="sample_valid_rows")
    status: ImportStatus


class ImportConfirmRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    skipInvalid: bool = Field(default=False, alias="skip_invalid")


class ImportCommitResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    batchId: str = Field(alias="batch_id")
    importType: ImportType = Field(alias="import_type")
    status: ImportStatus
    committedRows: int = Field(alias="committed_rows")
    skippedRows: int = Field(default=0, alias="skipped_rows")
    staleCycles: list[str] = Field(default_factory=list, alias="stale_cycles")
    message: str
