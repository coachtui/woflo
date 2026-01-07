from __future__ import annotations

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field


class ApiMeta(BaseModel):
    request_id: str | None = None


class WorkOrderStatus:
    NEW = "new"
    TRIAGE = "triage"
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    BLOCKED_PARTS = "blocked_parts"
    DONE = "done"
    CANCELED = "canceled"


WorkOrderLocation = Literal["shop", "field"]
WorkOrderStatusLiteral = Literal[
    "new",
    "triage",
    "scheduled",
    "in_progress",
    "blocked_parts",
    "done",
    "canceled",
]

TaskType = Literal["diagnose", "repair", "qa_test", "road_test", "cleanup", "paperwork"]
TaskStatus = Literal["todo", "scheduled", "in_progress", "done", "blocked"]


class Timestamped(BaseModel):
    created_at: datetime
    updated_at: datetime | None = None


class IdResponse(BaseModel):
    id: str = Field(..., description="UUID")


class UnitCreateRequest(BaseModel):
    unit_number: str
    asset_type: str
    customer_name_redacted: str | None = None


class UnitResponse(BaseModel):
    id: str
    unit_number: str
    asset_type: str
    customer_name_redacted: str | None


class TechnicianCreateRequest(BaseModel):
    name: str
    efficiency_multiplier: float = 1.0
    overtime_allowed: bool = True
    wip_limit: int = 3


class TechnicianResponse(BaseModel):
    id: str
    profile_id: str | None
    name: str
    efficiency_multiplier: float
    overtime_allowed: bool
    wip_limit: int


class WorkOrderCreateRequest(BaseModel):
    unit_id: str
    asset_type: str
    priority: int = Field(..., ge=1, le=5)
    due_date: date | None = None
    customer_commitment_at: datetime | None = None
    location: WorkOrderLocation
    notes: str | None = None
    parts_required: bool = False


class WorkOrderCreateResponse(IdResponse):
    status: WorkOrderStatusLiteral


class WorkOrderListItem(BaseModel):
    id: str
    unit_id: str
    asset_type: str
    priority: int
    due_date: date | None
    customer_commitment_at: datetime | None
    location: WorkOrderLocation
    notes: str | None
    status: WorkOrderStatusLiteral
    parts_required: bool
    parts_status: str
    parts_ready: bool
    parts_ready_at: datetime | None
    estimated_hours_low: float | None
    estimated_hours_high: float | None
    required_bay_type: str | None

    # derived flags
    is_blocked_parts: bool
    is_overdue: bool
    has_ai_enrichment: bool


class TaskPlanItem(BaseModel):
    type: TaskType
    duration_minutes_low: int = Field(..., ge=0)
    duration_minutes_high: int = Field(..., ge=0)


class TaskCreateReplaceRequest(BaseModel):
    tasks: list[TaskPlanItem]


class TaskResponse(BaseModel):
    id: str
    work_order_id: str
    type: TaskType
    status: TaskStatus
    required_skill: str | None
    required_skill_is_hard: bool
    required_bay_type: str | None
    earliest_start: datetime | None
    latest_finish: datetime | None
    duration_minutes_low: int
    duration_minutes_high: int
    lock_flag: bool
    locked_tech_id: str | None
    locked_bay_id: str | None
    locked_start_at: datetime | None
    locked_end_at: datetime | None


class TaskPatchRequest(BaseModel):
    # Dispatcher OR tech (tech is restricted in router/service)
    status: TaskStatus | None = None
    required_skill: str | None = None
    required_skill_is_hard: bool | None = None
    required_bay_type: str | None = None
    duration_minutes_low: int | None = Field(default=None, ge=0)
    duration_minutes_high: int | None = Field(default=None, ge=0)

    lock_flag: bool | None = None
    locked_tech_id: str | None = None
    locked_bay_id: str | None = None
    locked_start_at: datetime | None = None
    locked_end_at: datetime | None = None
