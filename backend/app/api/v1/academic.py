from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_role
from app.config.database import get_db
from app.config.logging import request_id_ctx_var
from app.models.enums import RoleEnum
from app.models.user import User
from app.schemas.academic import (
    AcademicYearCreate,
    AcademicYearResponse,
    AcademicYearUpdate,
    DepartmentCreate,
    DepartmentResponse,
    DepartmentUpdate,
    PaginatedAcademicYearsResponse,
    PaginatedDepartmentsResponse,
    PaginatedProgramsResponse,
    PaginatedSemestersResponse,
    ProgramCreate,
    ProgramResponse,
    ProgramUpdate,
    SemesterCreate,
    SemesterResponse,
    SemesterUpdate,
)
from app.services.academic_service import academic_service

router = APIRouter(prefix="/academic", tags=["Academic Structure"])


# ==============================================================================
# Departments (FR-02, Task P3.1)
# ==============================================================================
@router.get("/departments", response_model=PaginatedDepartmentsResponse)
def get_departments(
    page: int = Query(default=1, ge=1),
    pageSize: int = Query(default=20, ge=1, le=100, alias="pageSize"),
    status: str | None = Query(default=None),
    search: str | None = Query(default=None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> PaginatedDepartmentsResponse:
    items, total, total_pages = academic_service.get_departments(
        db=db, page=page, page_size=pageSize, status=status, search=search
    )
    return PaginatedDepartmentsResponse(
        items=[DepartmentResponse.model_validate(dept) for dept in items],
        total=total,
        page=page,
        pageSize=pageSize,
        totalPages=total_pages,
        hasNext=page < total_pages,
        hasPrev=page > 1,
    )


@router.post("/departments", response_model=DepartmentResponse, status_code=status.HTTP_201_CREATED)
def create_department(
    data: DepartmentCreate,
    current_user: User = Depends(require_role(RoleEnum.ADMIN)),
    db: Session = Depends(get_db),
) -> DepartmentResponse:
    dept = academic_service.create_department(
        db=db, data=data, actor=current_user, request_id=request_id_ctx_var.get()
    )
    return DepartmentResponse.model_validate(dept)


@router.get("/departments/{department_id}", response_model=DepartmentResponse)
def get_department(
    department_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> DepartmentResponse:
    dept = academic_service.get_department_by_id(db=db, dept_id=department_id)
    return DepartmentResponse.model_validate(dept)


@router.patch("/departments/{department_id}", response_model=DepartmentResponse)
def update_department(
    department_id: str,
    data: DepartmentUpdate,
    current_user: User = Depends(require_role(RoleEnum.ADMIN)),
    db: Session = Depends(get_db),
) -> DepartmentResponse:
    dept = academic_service.update_department(
        db=db,
        dept_id=department_id,
        data=data,
        actor=current_user,
        request_id=request_id_ctx_var.get(),
    )
    return DepartmentResponse.model_validate(dept)


@router.delete("/departments/{department_id}", response_model=DepartmentResponse)
def archive_department(
    department_id: str,
    current_user: User = Depends(require_role(RoleEnum.ADMIN)),
    db: Session = Depends(get_db),
) -> DepartmentResponse:
    dept = academic_service.archive_department(
        db=db, dept_id=department_id, actor=current_user, request_id=request_id_ctx_var.get()
    )
    return DepartmentResponse.model_validate(dept)


# ==============================================================================
# Academic Years (FR-02, Task P3.1)
# ==============================================================================
@router.get("/years", response_model=PaginatedAcademicYearsResponse)
def get_academic_years(
    page: int = Query(default=1, ge=1),
    pageSize: int = Query(default=20, ge=1, le=100, alias="pageSize"),
    status: str | None = Query(default=None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> PaginatedAcademicYearsResponse:
    items, total, total_pages = academic_service.get_academic_years(
        db=db, page=page, page_size=pageSize, status=status
    )
    return PaginatedAcademicYearsResponse(
        items=[AcademicYearResponse.model_validate(y) for y in items],
        total=total,
        page=page,
        pageSize=pageSize,
        totalPages=total_pages,
        hasNext=page < total_pages,
        hasPrev=page > 1,
    )


@router.post("/years", response_model=AcademicYearResponse, status_code=status.HTTP_201_CREATED)
def create_academic_year(
    data: AcademicYearCreate,
    current_user: User = Depends(require_role(RoleEnum.ADMIN)),
    db: Session = Depends(get_db),
) -> AcademicYearResponse:
    ay = academic_service.create_academic_year(
        db=db, data=data, actor=current_user, request_id=request_id_ctx_var.get()
    )
    return AcademicYearResponse.model_validate(ay)


@router.get("/years/{year_id}", response_model=AcademicYearResponse)
def get_academic_year(
    year_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AcademicYearResponse:
    ay = academic_service.get_academic_year_by_id(db=db, year_id=year_id)
    return AcademicYearResponse.model_validate(ay)


@router.patch("/years/{year_id}", response_model=AcademicYearResponse)
def update_academic_year(
    year_id: str,
    data: AcademicYearUpdate,
    current_user: User = Depends(require_role(RoleEnum.ADMIN)),
    db: Session = Depends(get_db),
) -> AcademicYearResponse:
    ay = academic_service.update_academic_year(
        db=db,
        year_id=year_id,
        data=data,
        actor=current_user,
        request_id=request_id_ctx_var.get(),
    )
    return AcademicYearResponse.model_validate(ay)


@router.delete("/years/{year_id}", response_model=AcademicYearResponse)
def archive_academic_year(
    year_id: str,
    current_user: User = Depends(require_role(RoleEnum.ADMIN)),
    db: Session = Depends(get_db),
) -> AcademicYearResponse:
    ay = academic_service.archive_academic_year(
        db=db, year_id=year_id, actor=current_user, request_id=request_id_ctx_var.get()
    )
    return AcademicYearResponse.model_validate(ay)


# ==============================================================================
# Semesters (FR-02, Task P3.1)
# ==============================================================================
@router.get("/semesters", response_model=PaginatedSemestersResponse)
def get_semesters(
    page: int = Query(default=1, ge=1),
    pageSize: int = Query(default=20, ge=1, le=100, alias="pageSize"),
    academicYearId: str | None = Query(default=None, alias="academicYearId"),
    status: str | None = Query(default=None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> PaginatedSemestersResponse:
    items, total, total_pages = academic_service.get_semesters(
        db=db,
        page=page,
        page_size=pageSize,
        academic_year_id=academicYearId,
        status=status,
    )
    return PaginatedSemestersResponse(
        items=[SemesterResponse.model_validate(s) for s in items],
        total=total,
        page=page,
        pageSize=pageSize,
        totalPages=total_pages,
        hasNext=page < total_pages,
        hasPrev=page > 1,
    )


@router.post("/semesters", response_model=SemesterResponse, status_code=status.HTTP_201_CREATED)
def create_semester(
    data: SemesterCreate,
    current_user: User = Depends(require_role(RoleEnum.ADMIN)),
    db: Session = Depends(get_db),
) -> SemesterResponse:
    sem = academic_service.create_semester(
        db=db, data=data, actor=current_user, request_id=request_id_ctx_var.get()
    )
    return SemesterResponse.model_validate(sem)


@router.get("/semesters/{semester_id}", response_model=SemesterResponse)
def get_semester(
    semester_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> SemesterResponse:
    sem = academic_service.get_semester_by_id(db=db, sem_id=semester_id)
    return SemesterResponse.model_validate(sem)


@router.patch("/semesters/{semester_id}", response_model=SemesterResponse)
def update_semester(
    semester_id: str,
    data: SemesterUpdate,
    current_user: User = Depends(require_role(RoleEnum.ADMIN)),
    db: Session = Depends(get_db),
) -> SemesterResponse:
    sem = academic_service.update_semester(
        db=db,
        sem_id=semester_id,
        data=data,
        actor=current_user,
        request_id=request_id_ctx_var.get(),
    )
    return SemesterResponse.model_validate(sem)


@router.delete("/semesters/{semester_id}", response_model=SemesterResponse)
def archive_semester(
    semester_id: str,
    current_user: User = Depends(require_role(RoleEnum.ADMIN)),
    db: Session = Depends(get_db),
) -> SemesterResponse:
    sem = academic_service.archive_semester(
        db=db, sem_id=semester_id, actor=current_user, request_id=request_id_ctx_var.get()
    )
    return SemesterResponse.model_validate(sem)


# ==============================================================================
# Programs (FR-02, Task P3.1)
# ==============================================================================
@router.get("/programs", response_model=PaginatedProgramsResponse)
def get_programs(
    page: int = Query(default=1, ge=1),
    pageSize: int = Query(default=20, ge=1, le=100, alias="pageSize"),
    departmentId: str | None = Query(default=None, alias="departmentId"),
    status: str | None = Query(default=None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> PaginatedProgramsResponse:
    items, total, total_pages = academic_service.get_programs(
        db=db,
        page=page,
        page_size=pageSize,
        department_id=departmentId,
        status=status,
    )
    return PaginatedProgramsResponse(
        items=[ProgramResponse.model_validate(p) for p in items],
        total=total,
        page=page,
        pageSize=pageSize,
        totalPages=total_pages,
        hasNext=page < total_pages,
        hasPrev=page > 1,
    )


@router.post("/programs", response_model=ProgramResponse, status_code=status.HTTP_201_CREATED)
def create_program(
    data: ProgramCreate,
    current_user: User = Depends(require_role(RoleEnum.ADMIN)),
    db: Session = Depends(get_db),
) -> ProgramResponse:
    prog = academic_service.create_program(
        db=db, data=data, actor=current_user, request_id=request_id_ctx_var.get()
    )
    return ProgramResponse.model_validate(prog)


@router.get("/programs/{program_id}", response_model=ProgramResponse)
def get_program(
    program_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ProgramResponse:
    prog = academic_service.get_program_by_id(db=db, prog_id=program_id)
    return ProgramResponse.model_validate(prog)


@router.patch("/programs/{program_id}", response_model=ProgramResponse)
def update_program(
    program_id: str,
    data: ProgramUpdate,
    current_user: User = Depends(require_role(RoleEnum.ADMIN)),
    db: Session = Depends(get_db),
) -> ProgramResponse:
    prog = academic_service.update_program(
        db=db,
        prog_id=program_id,
        data=data,
        actor=current_user,
        request_id=request_id_ctx_var.get(),
    )
    return ProgramResponse.model_validate(prog)


@router.delete("/programs/{program_id}", response_model=ProgramResponse)
def archive_program(
    program_id: str,
    current_user: User = Depends(require_role(RoleEnum.ADMIN)),
    db: Session = Depends(get_db),
) -> ProgramResponse:
    prog = academic_service.archive_program(
        db=db, prog_id=program_id, actor=current_user, request_id=request_id_ctx_var.get()
    )
    return ProgramResponse.model_validate(prog)
