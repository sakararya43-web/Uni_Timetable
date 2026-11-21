"""Conflict Graph Schemas for API Requests, Responses, and Exports.

PRD §11 (FR-07), §18.6, §23 (Privacy: no student identities in standard graph payloads), Tasks P6.1, P6.11.
"""

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class GraphNode(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: str  # Exam ID
    subjectId: str = Field(alias="subject_id")
    subjectCode: str = Field(alias="subject_code")
    subjectName: str = Field(alias="subject_name")
    departmentId: str = Field(alias="department_id")
    departmentCode: str | None = Field(default=None, alias="department_code")
    semester: int
    enrollmentCount: int = Field(alias="enrollment_count")
    degree: int


class GraphEdge(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: str
    examIdA: str = Field(alias="exam_id_a")
    examIdB: str = Field(alias="exam_id_b")
    subjectCodeA: str = Field(alias="subject_code_a")
    subjectCodeB: str = Field(alias="subject_code_b")
    sharedStudentCount: int = Field(alias="shared_student_count")


class GraphStatsResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    vertexCount: int = Field(alias="vertex_count")
    edgeCount: int = Field(alias="edge_count")
    density: float
    avgDegree: float = Field(alias="avg_degree")
    maxDegree: int = Field(alias="max_degree")
    minDegree: int = Field(alias="min_degree")
    isolatedVertices: list[str] = Field(default_factory=list, alias="isolated_vertices")
    isolatedCount: int = Field(default=0, alias="isolated_count")
    connectedComponentsCount: int = Field(alias="connected_components_count")
    largestComponentSize: int = Field(alias="largest_component_size")
    degreeHistogram: dict[str, int] = Field(default_factory=dict, alias="degree_histogram")
    chromaticLowerBound: int = Field(alias="chromatic_lower_bound")
    topExamsByDegree: list[dict[str, Any]] = Field(default_factory=list, alias="top_exams_by_degree")


class ConflictGraphResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    snapshotId: str = Field(alias="snapshot_id")
    cycleId: str = Field(alias="cycle_id")
    version: int
    isStale: bool = Field(alias="is_stale")
    currentEnrollmentHash: str = Field(alias="current_enrollment_hash")
    snapshotEnrollmentHash: str = Field(alias="snapshot_enrollment_hash")
    stats: GraphStatsResponse
    nodes: list[GraphNode]
    edges: list[GraphEdge]


class GraphBuildResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    snapshotId: str = Field(alias="snapshot_id")
    cycleId: str = Field(alias="cycle_id")
    version: int
    isNew: bool = Field(alias="is_new")
    isStale: bool = Field(alias="is_stale")
    stats: GraphStatsResponse
    validation: dict[str, Any]


class SharedStudentInfo(BaseModel):
    """Student identity info for privileged staff conflict drilldown only (FR-07, PRD §23)."""
    model_config = ConfigDict(populate_by_name=True)

    studentId: str = Field(alias="student_id")
    studentNumber: str = Field(alias="student_number")
    fullName: str = Field(alias="full_name")
    email: str | None = None
    programName: str | None = Field(default=None, alias="program_name")


class ConflictEdgeDetailResponse(BaseModel):
    """Detailed drilldown of a single conflict edge with shared students (Task P6.11)."""
    model_config = ConfigDict(populate_by_name=True)

    edgeId: str = Field(alias="edge_id")
    examIdA: str = Field(alias="exam_id_a")
    examIdB: str = Field(alias="exam_id_b")
    subjectCodeA: str = Field(alias="subject_code_a")
    subjectCodeB: str = Field(alias="subject_code_b")
    subjectNameA: str = Field(alias="subject_name_a")
    subjectNameB: str = Field(alias="subject_name_b")
    sharedStudentCount: int = Field(alias="shared_student_count")
    students: list[SharedStudentInfo]
