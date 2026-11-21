from enum import Enum


class RoleEnum(str, Enum):
    ADMIN = "admin"
    COORDINATOR = "coordinator"
    FACULTY = "faculty"
    STUDENT = "student"


class UserStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    ARCHIVED = "archived"


class EntityStatus(str, Enum):
    ACTIVE = "active"
    ARCHIVED = "archived"


class EnrollmentStatus(str, Enum):
    ACTIVE = "active"
    WITHDRAWN = "withdrawn"


class CycleStatus(str, Enum):
    DRAFT = "Draft"
    GENERATED = "Generated"
    REVIEWED = "Reviewed"
    PUBLISHED = "Published"
    ARCHIVED = "Archived"


class ScheduleStatus(str, Enum):
    CANDIDATE = "Candidate"
    REVIEWED = "Reviewed"
    PUBLISHED = "Published"
    ARCHIVED = "Archived"


class ScheduleRunStatus(str, Enum):
    RUNNING = "running"
    SUCCESS = "success"
    SUCCESS_WITH_WARNINGS = "success_with_warnings"
    INFEASIBLE_INSUFFICIENT_SLOTS = "infeasible_insufficient_slots"
    INVALID_DATA_OR_ALGORITHM_ERROR = "invalid_data_or_algorithm_error"
    CANCELLED = "cancelled"
    FAILED = "failed"


class ImportType(str, Enum):
    STUDENTS = "students"
    SUBJECTS = "subjects"
    ENROLLMENTS = "enrollments"


class ImportStatus(str, Enum):
    PREVIEW = "preview"
    COMMITTED = "committed"
    CANCELLED = "cancelled"
    FAILED = "failed"


class AuditAction(str, Enum):
    LOGIN = "LOGIN"
    LOGOUT = "LOGOUT"
    LOGIN_FAILED = "LOGIN_FAILED"
    IMPORT_PREVIEW = "IMPORT_PREVIEW"
    IMPORT_COMMIT = "IMPORT_COMMIT"
    IMPORT_CANCEL = "IMPORT_CANCEL"
    IMPORT_FAILED = "IMPORT_FAILED"
    USER_CREATE = "USER_CREATE"
    USER_UPDATE = "USER_UPDATE"
    USER_ACTIVATE = "USER_ACTIVATE"
    USER_DEACTIVATE = "USER_DEACTIVATE"
    USER_PASSWORD_RESET = "USER_PASSWORD_RESET"
    SUBJECT_CREATE = "SUBJECT_CREATE"
    SUBJECT_UPDATE = "SUBJECT_UPDATE"
    SUBJECT_ARCHIVE = "SUBJECT_ARCHIVE"
    STUDENT_CREATE = "STUDENT_CREATE"
    STUDENT_UPDATE = "STUDENT_UPDATE"
    STUDENT_ARCHIVE = "STUDENT_ARCHIVE"
    ENROLLMENT_CREATE = "ENROLLMENT_CREATE"
    ENROLLMENT_WITHDRAW = "ENROLLMENT_WITHDRAW"
    CYCLE_CREATE = "CYCLE_CREATE"
    CYCLE_UPDATE = "CYCLE_UPDATE"
    CYCLE_ARCHIVE = "CYCLE_ARCHIVE"
    SLOTS_GENERATE = "SLOTS_GENERATE"
    GRAPH_BUILD = "GRAPH_BUILD"
    GRAPH_DRILLDOWN = "GRAPH_DRILLDOWN"
    SCHEDULE_RUN = "SCHEDULE_RUN"
    SCHEDULE_SAVE = "SCHEDULE_SAVE"
    SCHEDULE_EDIT = "SCHEDULE_EDIT"
    SCHEDULE_CLONE = "SCHEDULE_CLONE"
    SCHEDULE_ARCHIVE = "SCHEDULE_ARCHIVE"
    SCHEDULE_REGENERATE = "SCHEDULE_REGENERATE"
    EXAM_LOCK = "EXAM_LOCK"
    EXAM_UNLOCK = "EXAM_UNLOCK"
    SCHEDULE_VALIDATE = "SCHEDULE_VALIDATE"
    SCHEDULE_PUBLISH = "SCHEDULE_PUBLISH"
    EXPORT = "EXPORT"
    ADMIN_OP_FAILED = "ADMIN_OP_FAILED"


def enum_val(item: object) -> str:
    """Safely return string value for enums or plain strings."""
    if hasattr(item, "value"):
        return str(item.value)
    return str(item)
