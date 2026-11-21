
from fastapi import APIRouter, Depends, File, Query, Response, UploadFile, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_role
from app.config.database import get_db
from app.config.logging import request_id_ctx_var
from app.config.settings import Settings, get_settings
from app.models.audit import ImportBatch
from app.models.enums import ImportType, RoleEnum
from app.models.user import User
from app.schemas.import_csv import (
    ImportCommitResponse,
    ImportConfirmRequest,
    ImportPreviewResponse,
    RowValidationError,
)
from app.services.import_service import import_service

router = APIRouter(tags=["CSV Imports"])


# ==============================================================================
# Helper to handle upload preview vs direct commit
# ==============================================================================
def _handle_upload_mode(
    db: Session,
    import_type: ImportType,
    file_bytes: bytes,
    file_name: str,
    actor: User,
    mode: str,
    skip_invalid: bool,
    cycle_id: str | None,
    settings: Settings,
    request_id: str | None,
) -> ImportPreviewResponse | ImportCommitResponse:
    preview = import_service.preview_import(
        db=db,
        import_type=import_type,
        raw_bytes=file_bytes,
        file_name=file_name,
        actor=actor,
        cycle_id=cycle_id,
        max_size_bytes=settings.MAX_UPLOAD_SIZE_BYTES,
        max_rows=settings.MAX_CSV_ROWS,
        request_id=request_id,
    )

    if mode.lower() == "commit":
        return import_service.confirm_import(
            db=db,
            batch_id=preview.batchId,
            actor=actor,
            skip_invalid=skip_invalid,
            request_id=request_id,
        )

    return preview


# ==============================================================================
# Upload Endpoints (Task P4.1)
# ==============================================================================
@router.post(
    "/students/import",
    response_model=ImportPreviewResponse | ImportCommitResponse,
    status_code=status.HTTP_200_OK,
)
async def import_students(
    file: UploadFile = File(...),
    mode: str = Query(default="preview", description="'preview' (validate only) or 'commit'"),
    skipInvalid: bool = Query(default=False, alias="skipInvalid"),
    current_user: User = Depends(require_role(RoleEnum.ADMIN, RoleEnum.COORDINATOR)),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> ImportPreviewResponse | ImportCommitResponse:
    file_bytes = await file.read()
    return _handle_upload_mode(
        db=db,
        import_type=ImportType.STUDENTS,
        file_bytes=file_bytes,
        file_name=file.filename or "students.csv",
        actor=current_user,
        mode=mode,
        skip_invalid=skipInvalid,
        cycle_id=None,
        settings=settings,
        request_id=request_id_ctx_var.get(),
    )


@router.post(
    "/subjects/import",
    response_model=ImportPreviewResponse | ImportCommitResponse,
    status_code=status.HTTP_200_OK,
)
async def import_subjects(
    file: UploadFile = File(...),
    mode: str = Query(default="preview", description="'preview' (validate only) or 'commit'"),
    skipInvalid: bool = Query(default=False, alias="skipInvalid"),
    current_user: User = Depends(require_role(RoleEnum.ADMIN, RoleEnum.COORDINATOR)),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> ImportPreviewResponse | ImportCommitResponse:
    file_bytes = await file.read()
    return _handle_upload_mode(
        db=db,
        import_type=ImportType.SUBJECTS,
        file_bytes=file_bytes,
        file_name=file.filename or "subjects.csv",
        actor=current_user,
        mode=mode,
        skip_invalid=skipInvalid,
        cycle_id=None,
        settings=settings,
        request_id=request_id_ctx_var.get(),
    )


@router.post(
    "/enrollments/import",
    response_model=ImportPreviewResponse | ImportCommitResponse,
    status_code=status.HTTP_200_OK,
)
async def import_enrollments(
    file: UploadFile = File(...),
    cycleId: str | None = Query(default=None, alias="cycleId"),
    mode: str = Query(default="preview", description="'preview' (validate only) or 'commit'"),
    skipInvalid: bool = Query(default=False, alias="skipInvalid"),
    current_user: User = Depends(require_role(RoleEnum.ADMIN, RoleEnum.COORDINATOR)),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> ImportPreviewResponse | ImportCommitResponse:
    file_bytes = await file.read()
    return _handle_upload_mode(
        db=db,
        import_type=ImportType.ENROLLMENTS,
        file_bytes=file_bytes,
        file_name=file.filename or "enrollments.csv",
        actor=current_user,
        mode=mode,
        skip_invalid=skipInvalid,
        cycle_id=cycleId,
        settings=settings,
        request_id=request_id_ctx_var.get(),
    )


# ==============================================================================
# Batch Management & Confirmation (Tasks P4.1, P4.7, P4.11)
# ==============================================================================
@router.post("/imports/{batch_id}/confirm", response_model=ImportCommitResponse)
def confirm_import(
    batch_id: str,
    payload: ImportConfirmRequest = ImportConfirmRequest(),
    current_user: User = Depends(require_role(RoleEnum.ADMIN, RoleEnum.COORDINATOR)),
    db: Session = Depends(get_db),
) -> ImportCommitResponse:
    """Confirm and commit staged import batch (Task P4.1, P4.7)."""
    return import_service.confirm_import(
        db=db,
        batch_id=batch_id,
        actor=current_user,
        skip_invalid=payload.skipInvalid,
        request_id=request_id_ctx_var.get(),
    )


@router.post("/imports/{batch_id}/cancel", response_model=ImportCommitResponse)
def cancel_import(
    batch_id: str,
    current_user: User = Depends(require_role(RoleEnum.ADMIN, RoleEnum.COORDINATOR)),
    db: Session = Depends(get_db),
) -> ImportCommitResponse:
    """Cancel and discard a staged import batch (Task P4.11)."""
    return import_service.cancel_batch(
        db=db, batch_id=batch_id, actor=current_user, request_id=request_id_ctx_var.get()
    )


@router.get("/imports/{batch_id}", response_model=ImportPreviewResponse)
def get_import_batch(
    batch_id: str,
    current_user: User = Depends(require_role(RoleEnum.ADMIN, RoleEnum.COORDINATOR)),
    db: Session = Depends(get_db),
) -> ImportPreviewResponse:
    """Get status and details of an import batch."""
    batch = db.get(ImportBatch, batch_id)
    if not batch:
        from app.middleware.error_handler import DomainException

        raise DomainException(
            code="IMPORT_BATCH_NOT_FOUND",
            message=f"Import batch '{batch_id}' not found.",
            status_code=404,
        )

    errors = [
        RowValidationError.model_validate(e)
        for e in batch.errors_json.get("errors", [])
    ]
    staged = batch.errors_json.get("staged_rows", [])

    return ImportPreviewResponse(
        batch_id=batch.id,
        import_type=batch.import_type,
        cycle_id=batch.cycle_id,
        file_name=batch.file_name,
        total_rows=batch.total_rows,
        valid_rows=batch.valid_rows,
        invalid_rows=batch.invalid_rows,
        duplicate_count=0,
        unknown_reference_count=0,
        already_imported=False,
        warning_message=None,
        errors=errors,
        sample_valid_rows=staged[:10],
        status=batch.status,
    )


@router.get("/imports/{batch_id}/errors/download")
def download_import_errors(
    batch_id: str,
    current_user: User = Depends(require_role(RoleEnum.ADMIN, RoleEnum.COORDINATOR)),
    db: Session = Depends(get_db),
) -> Response:
    """Download CSV error report for a batch with correction guidance (Task P4.6)."""
    csv_content = import_service.generate_error_csv(db=db, batch_id=batch_id)
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=import_errors_{batch_id}.csv"},
    )


@router.get("/imports/templates/{import_type}")
def download_csv_template(
    import_type: ImportType,
    current_user: User = Depends(get_current_user),
) -> Response:
    """Download example CSV templates matching PRD §FR-05 (Task P4.15)."""
    csv_content = import_service.get_csv_template(import_type)
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=template_{import_type.value}.csv"},
    )
