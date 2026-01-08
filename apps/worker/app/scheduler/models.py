"""Data models for scheduler."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass
class Task:
    """A task to be scheduled."""
    
    id: str
    work_order_id: str
    type: str
    status: str
    required_skill: str | None
    required_skill_is_hard: bool
    required_bay_type: str | None
    earliest_start: datetime | None
    latest_finish: datetime | None
    duration_minutes_low: int
    duration_minutes_high: int
    
    # Lock information
    is_locked: bool
    locked_tech_id: str | None
    locked_bay_id: str | None
    locked_start_at: datetime | None
    locked_end_at: datetime | None
    
    # Computed values
    duration_minutes: int  # Average of low/high
    
    @classmethod
    def from_row(cls, row: dict[str, Any]) -> Task:
        """Create Task from database row."""
        duration_avg = (row["duration_minutes_low"] + row["duration_minutes_high"]) // 2
        
        return cls(
            id=row["id"],
            work_order_id=row["work_order_id"],
            type=row["type"],
            status=row["status"],
            required_skill=row["required_skill"],
            required_skill_is_hard=row["required_skill_is_hard"],
            required_bay_type=row["required_bay_type"],
            earliest_start=row["earliest_start"],
            latest_finish=row["latest_finish"],
            duration_minutes_low=row["duration_minutes_low"],
            duration_minutes_high=row["duration_minutes_high"],
            is_locked=row["lock_flag"],
            locked_tech_id=row["locked_tech_id"],
            locked_bay_id=row["locked_bay_id"],
            locked_start_at=row["locked_start_at"],
            locked_end_at=row["locked_end_at"],
            duration_minutes=duration_avg,
        )


@dataclass
class Technician:
    """A technician who can perform tasks."""
    
    id: str
    name: str
    skills: list[str]
    efficiency_multiplier: float
    wip_limit: int
    
    @classmethod
    def from_row(cls, row: dict[str, Any], skills: list[str]) -> Technician:
        """Create Technician from database row."""
        return cls(
            id=row["id"],
            name=row["name"],
            skills=skills,
            efficiency_multiplier=float(row["efficiency_multiplier"]),
            wip_limit=row["wip_limit"],
        )


@dataclass
class Bay:
    """A bay where work is performed."""
    
    id: str
    name: str
    bay_type: str
    capacity: int
    is_active: bool
    
    @classmethod
    def from_row(cls, row: dict[str, Any]) -> Bay:
        """Create Bay from database row."""
        return cls(
            id=row["id"],
            name=row["name"],
            bay_type=row["bay_type"],
            capacity=row["capacity"],
            is_active=row["is_active"],
        )


@dataclass
class WorkOrder:
    """Work order information for tasks."""
    
    id: str
    priority: int
    due_date: datetime | None
    parts_ready: bool
    
    @classmethod
    def from_row(cls, row: dict[str, Any]) -> WorkOrder:
        """Create WorkOrder from database row."""
        return cls(
            id=row["id"],
            priority=row["priority"],
            due_date=row["due_date"],
            parts_ready=row["parts_ready"],
        )


@dataclass
class ScheduleInput:
    """Input data for scheduler."""
    
    org_id: str
    schedule_run_id: str
    horizon_start: datetime
    horizon_end: datetime
    tasks: list[Task]
    technicians: list[Technician]
    bays: list[Bay]
    work_orders: dict[str, WorkOrder]  # wo_id -> WorkOrder
    
    def get_locked_tasks(self) -> list[Task]:
        """Get all locked tasks."""
        return [t for t in self.tasks if t.is_locked]
    
    def get_unlocked_tasks(self) -> list[Task]:
        """Get all unlocked tasks."""
        return [t for t in self.tasks if not t.is_locked]


@dataclass
class ScheduleItem:
    """A scheduled item (task assignment)."""
    
    task_id: str
    technician_id: str
    bay_id: str
    start_at: datetime
    end_at: datetime
    is_locked: bool
    why: dict[str, Any] | None = None


@dataclass
class ObjectiveBreakdown:
    """Breakdown of objective function components."""
    
    total_penalty: int
    due_date_penalty: int
    priority_penalty: int
    skill_mismatch_penalty: int
    parts_not_ready_penalty: int
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON storage."""
        return {
            "total_penalty": self.total_penalty,
            "due_date_penalty": self.due_date_penalty,
            "priority_penalty": self.priority_penalty,
            "skill_mismatch_penalty": self.skill_mismatch_penalty,
            "parts_not_ready_penalty": self.parts_not_ready_penalty,
        }


@dataclass
class ScheduleResult:
    """Result of scheduling operation."""
    
    status: str  # succeeded, failed, infeasible
    items: list[ScheduleItem]
    solver_wall_time_ms: int
    objective_value: int | None
    objective_breakdown: ObjectiveBreakdown | None
    infeasible_reason: str | None = None
