"""OR-Tools CP-SAT scheduler implementation."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any

from ortools.sat.python import cp_model

from app.scheduler.models import (
    ObjectiveBreakdown,
    ScheduleInput,
    ScheduleItem,
    ScheduleResult,
    Task,
)

logger = logging.getLogger(__name__)


def datetime_to_minutes(dt: datetime | Any, base: datetime | Any) -> int:
    """Convert datetime to minutes from base."""
    # Handle datetime.date objects by converting to datetime
    from datetime import date
    if isinstance(dt, date) and not isinstance(dt, datetime):
        dt = datetime.combine(dt, datetime.min.time())
    if isinstance(base, date) and not isinstance(base, datetime):
        base = datetime.combine(base, datetime.min.time())
    
    return int((dt - base).total_seconds() / 60)


def minutes_to_datetime(minutes: int, base: datetime) -> datetime:
    """Convert minutes from base to datetime."""
    return base + timedelta(minutes=minutes)


class SchedulerModel:
    """CP-SAT scheduler model."""
    
    def __init__(self, input_data: ScheduleInput):
        """Initialize scheduler model."""
        self.input = input_data
        self.model = cp_model.CpModel()
        
        # Time horizon in minutes
        self.horizon_minutes = datetime_to_minutes(
            input_data.horizon_end,
            input_data.horizon_start,
        )
        
        # Decision variables: task intervals
        self.task_intervals: dict[str, Any] = {}  # task_id -> interval_var
        self.task_starts: dict[str, Any] = {}     # task_id -> start_var
        self.task_ends: dict[str, Any] = {}       # task_id -> end_var
        
        # Assignment variables
        self.task_tech_assignments: dict[str, Any] = {}  # task_id -> tech_id_var
        self.task_bay_assignments: dict[str, Any] = {}   # task_id -> bay_id_var
        
        # Tech/bay ID mappings
        self.tech_id_to_index = {t.id: i for i, t in enumerate(input_data.technicians)}
        self.bay_id_to_index = {b.id: i for i, b in enumerate(input_data.bays)}
        
        # Penalty tracking for objective breakdown
        self.penalty_vars: dict[str, Any] = {}
        
    def build(self) -> None:
        """Build the complete CP-SAT model."""
        logger.info("building_cp_sat_model")
        
        self._create_task_variables()
        self._add_locked_task_constraints()
        self._add_tech_no_overlap_constraints()
        self._add_bay_no_overlap_constraints()
        self._add_skill_constraints()
        self._add_bay_type_constraints()
        self._add_time_window_constraints()
        self._add_parts_constraints()
        self._create_objective()
        
        logger.info("cp_sat_model_built")
    
    def _create_task_variables(self) -> None:
        """Create decision variables for all tasks."""
        for task in self.input.get_unlocked_tasks():
            # Task duration
            duration = task.duration_minutes
            
            # Create interval variable
            start_var = self.model.NewIntVar(0, self.horizon_minutes, f"start_{task.id}")
            end_var = self.model.NewIntVar(0, self.horizon_minutes, f"end_{task.id}")
            interval_var = self.model.NewIntervalVar(
                start_var,
                duration,
                end_var,
                f"interval_{task.id}",
            )
            
            self.task_starts[task.id] = start_var
            self.task_ends[task.id] = end_var
            self.task_intervals[task.id] = interval_var
            
            # Assignment variables
            tech_var = self.model.NewIntVar(
                0,
                len(self.input.technicians) - 1,
                f"tech_{task.id}",
            )
            bay_var = self.model.NewIntVar(
                0,
                len(self.input.bays) - 1,
                f"bay_{task.id}",
            )
            
            self.task_tech_assignments[task.id] = tech_var
            self.task_bay_assignments[task.id] = bay_var
    
    def _add_locked_task_constraints(self) -> None:
        """Handle locked tasks - they are fixed and block resources."""
        locked_tasks = self.input.get_locked_tasks()
        
        if not locked_tasks:
            return
        
        logger.info("adding_locked_task_constraints", extra={"count": len(locked_tasks)})
        
        for task in locked_tasks:
            # Locked tasks are not scheduled by solver, but we need to
            # prevent other tasks from overlapping with them
            # We'll handle this in no-overlap constraints
            pass
    
    def _add_tech_no_overlap_constraints(self) -> None:
        """Add no-overlap constraints for technicians."""
        logger.info("adding_tech_no_overlap_constraints")
        
        for tech in self.input.technicians:
            tech_index = self.tech_id_to_index[tech.id]
            
            # Collect intervals for this tech
            intervals = []
            
            # Locked tasks assigned to this tech
            for task in self.input.get_locked_tasks():
                if task.locked_tech_id == tech.id:
                    # Create fixed interval for locked task
                    start_min = datetime_to_minutes(
                        task.locked_start_at,
                        self.input.horizon_start,
                    )
                    end_min = datetime_to_minutes(
                        task.locked_end_at,
                        self.input.horizon_start,
                    )
                    duration = end_min - start_min
                    
                    locked_interval = self.model.NewFixedSizeIntervalVar(
                        start_min,
                        duration,
                        f"locked_{task.id}",
                    )
                    intervals.append(locked_interval)
            
            # Unlocked tasks that could be assigned to this tech
            for task in self.input.get_unlocked_tasks():
                # Only add to this tech's no-overlap if actually assigned
                tech_var = self.task_tech_assignments[task.id]
                interval_var = self.task_intervals[task.id]
                
                # Create optional interval that's only active when assigned to this tech
                is_assigned = self.model.NewBoolVar(f"tech_{tech.id}_has_{task.id}")
                self.model.Add(tech_var == tech_index).OnlyEnforceIf(is_assigned)
                self.model.Add(tech_var != tech_index).OnlyEnforceIf(is_assigned.Not())
                
                optional_interval = self.model.NewOptionalIntervalVar(
                    self.task_starts[task.id],
                    task.duration_minutes,
                    self.task_ends[task.id],
                    is_assigned,
                    f"tech_{tech.id}_interval_{task.id}",
                )
                intervals.append(optional_interval)
            
            # Add no-overlap constraint
            if intervals:
                self.model.AddNoOverlap(intervals)
    
    def _add_bay_no_overlap_constraints(self) -> None:
        """Add no-overlap constraints for bays."""
        logger.info("adding_bay_no_overlap_constraints")
        
        for bay in self.input.bays:
            bay_index = self.bay_id_to_index[bay.id]
            
            # Collect intervals for this bay
            intervals = []
            
            # Locked tasks assigned to this bay
            for task in self.input.get_locked_tasks():
                if task.locked_bay_id == bay.id:
                    start_min = datetime_to_minutes(
                        task.locked_start_at,
                        self.input.horizon_start,
                    )
                    end_min = datetime_to_minutes(
                        task.locked_end_at,
                        self.input.horizon_start,
                    )
                    duration = end_min - start_min
                    
                    locked_interval = self.model.NewFixedSizeIntervalVar(
                        start_min,
                        duration,
                        f"locked_bay_{task.id}",
                    )
                    intervals.append(locked_interval)
            
            # Unlocked tasks that could be assigned to this bay
            for task in self.input.get_unlocked_tasks():
                bay_var = self.task_bay_assignments[task.id]
                
                # Create optional interval
                is_assigned = self.model.NewBoolVar(f"bay_{bay.id}_has_{task.id}")
                self.model.Add(bay_var == bay_index).OnlyEnforceIf(is_assigned)
                self.model.Add(bay_var != bay_index).OnlyEnforceIf(is_assigned.Not())
                
                optional_interval = self.model.NewOptionalIntervalVar(
                    self.task_starts[task.id],
                    task.duration_minutes,
                    self.task_ends[task.id],
                    is_assigned,
                    f"bay_{bay.id}_interval_{task.id}",
                )
                intervals.append(optional_interval)
            
            # Add no-overlap constraint
            if intervals:
                self.model.AddNoOverlap(intervals)
    
    def _add_skill_constraints(self) -> None:
        """Add skill matching constraints and penalties."""
        logger.info("adding_skill_constraints")
        
        for task in self.input.get_unlocked_tasks():
            if not task.required_skill:
                continue
            
            tech_var = self.task_tech_assignments[task.id]
            
            # Find techs with this skill
            techs_with_skill = [
                self.tech_id_to_index[tech.id]
                for tech in self.input.technicians
                if task.required_skill in tech.skills
            ]
            
            if task.required_skill_is_hard:
                # Hard constraint: must assign to tech with skill
                if not techs_with_skill:
                    # No tech has this skill - model will be infeasible
                    logger.warning(
                        "no_tech_with_required_skill",
                        extra={"task_id": task.id, "skill": task.required_skill},
                    )
                else:
                    self.model.AddAllowedAssignments(tech_var, [(t,) for t in techs_with_skill])
            else:
                # Soft constraint: add penalty if skill mismatch
                has_skill = self.model.NewBoolVar(f"has_skill_{task.id}")
                if techs_with_skill:
                    self.model.AddAllowedAssignments(
                        [tech_var],
                        [(t,) for t in techs_with_skill],
                    ).OnlyEnforceIf(has_skill)
                else:
                    # No one has skill, always mismatch
                    self.model.Add(has_skill == 0)
                
                # Penalty for skill mismatch
                penalty_var = self.model.NewIntVar(0, 100, f"skill_penalty_{task.id}")
                self.model.Add(penalty_var == 50).OnlyEnforceIf(has_skill.Not())
                self.model.Add(penalty_var == 0).OnlyEnforceIf(has_skill)
                self.penalty_vars[f"skill_mismatch_{task.id}"] = penalty_var
    
    def _add_bay_type_constraints(self) -> None:
        """Add bay type constraints."""
        logger.info("adding_bay_type_constraints")
        
        for task in self.input.get_unlocked_tasks():
            if not task.required_bay_type:
                continue
            
            bay_var = self.task_bay_assignments[task.id]
            
            # Find bays with this type
            bays_with_type = [
                self.bay_id_to_index[bay.id]
                for bay in self.input.bays
                if bay.bay_type == task.required_bay_type
            ]
            
            if not bays_with_type:
                logger.warning(
                    "no_bay_with_required_type",
                    extra={"task_id": task.id, "bay_type": task.required_bay_type},
                )
            else:
                # Hard constraint
                self.model.AddAllowedAssignments(bay_var, [(b,) for b in bays_with_type])
    
    def _add_time_window_constraints(self) -> None:
        """Add time window constraints (earliest start, latest finish)."""
        logger.info("adding_time_window_constraints")
        
        for task in self.input.get_unlocked_tasks():
            # Earliest start
            if task.earliest_start:
                earliest_minutes = datetime_to_minutes(
                    task.earliest_start,
                    self.input.horizon_start,
                )
                if earliest_minutes > 0:
                    self.model.Add(self.task_starts[task.id] >= earliest_minutes)
            
            # Latest finish
            if task.latest_finish:
                latest_minutes = datetime_to_minutes(
                    task.latest_finish,
                    self.input.horizon_start,
                )
                if latest_minutes < self.horizon_minutes:
                    self.model.Add(self.task_ends[task.id] <= latest_minutes)
    
    def _add_parts_constraints(self) -> None:
        """Add parts readiness constraints (gate)."""
        logger.info("adding_parts_constraints")
        
        for task in self.input.get_unlocked_tasks():
            wo = self.input.work_orders.get(task.work_order_id)
            if not wo:
                continue
            
            if not wo.parts_ready:
                # Add penalty for scheduling before parts ready
                penalty_var = self.model.NewIntVar(0, 200, f"parts_penalty_{task.id}")
                self.model.Add(penalty_var == 100)  # Fixed penalty
                self.penalty_vars[f"parts_not_ready_{task.id}"] = penalty_var
    
    def _create_objective(self) -> None:
        """Create objective function to minimize penalties."""
        logger.info("creating_objective")
        
        objective_terms = []
        
        # Due date penalties
        for task in self.input.get_unlocked_tasks():
            wo = self.input.work_orders.get(task.work_order_id)
            if not wo or not wo.due_date:
                continue
            
            due_minutes = datetime_to_minutes(wo.due_date, self.input.horizon_start)
            
            # Penalty if task finishes after due date
            is_late = self.model.NewBoolVar(f"late_{task.id}")
            self.model.Add(self.task_ends[task.id] > due_minutes).OnlyEnforceIf(is_late)
            self.model.Add(self.task_ends[task.id] <= due_minutes).OnlyEnforceIf(is_late.Not())
            
            # Penalty scales with priority (higher priority = higher penalty)
            penalty_weight = wo.priority * 100
            penalty_var = self.model.NewIntVar(0, penalty_weight, f"due_penalty_{task.id}")
            self.model.Add(penalty_var == penalty_weight).OnlyEnforceIf(is_late)
            self.model.Add(penalty_var == 0).OnlyEnforceIf(is_late.Not())
            
            self.penalty_vars[f"due_date_{task.id}"] = penalty_var
            objective_terms.append(penalty_var)
        
        # Priority penalties (prefer higher priority earlier)
        for task in self.input.get_unlocked_tasks():
            wo = self.input.work_orders.get(task.work_order_id)
            if not wo:
                continue
            
            # Small penalty based on start time, scaled inversely by priority
            # Higher priority tasks get penalized more for late starts
            priority_weight = (6 - wo.priority)  # Invert priority (5->1, 1->5)
            penalty_var = self.model.NewIntVar(
                0,
                self.horizon_minutes * priority_weight,
                f"priority_penalty_{task.id}",
            )
            # Penalty = start_time * priority_weight / 100
            self.model.AddDivisionEquality(
                penalty_var,
                self.task_starts[task.id] * priority_weight,
                100,
            )
            self.penalty_vars[f"priority_{task.id}"] = penalty_var
            objective_terms.append(penalty_var)
        
        # Add all penalty variables from constraints
        objective_terms.extend(self.penalty_vars.values())
        
        # Minimize total penalty
        self.model.Minimize(sum(objective_terms))
    
    def solve(self, time_limit_seconds: int = 30) -> ScheduleResult:
        """
        Solve the CP-SAT model.
        
        Args:
            time_limit_seconds: Maximum solve time
        
        Returns:
            ScheduleResult with solution or infeasibility info
        """
        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = time_limit_seconds
        solver.parameters.log_search_progress = False
        
        logger.info("solving_cp_sat_model", extra={"time_limit": time_limit_seconds})
        
        status = solver.Solve(self.model)
        wall_time_ms = int(solver.WallTime() * 1000)
        
        logger.info(
            "cp_sat_solve_complete",
            extra={
                "status": solver.StatusName(status),
                "wall_time_ms": wall_time_ms,
            },
        )
        
        if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
            # Extract solution
            items = self._extract_solution(solver)
            
            # Calculate objective breakdown
            objective_breakdown = self._calculate_objective_breakdown(solver)
            
            return ScheduleResult(
                status="succeeded",
                items=items,
                solver_wall_time_ms=wall_time_ms,
                objective_value=int(solver.ObjectiveValue()),
                objective_breakdown=objective_breakdown,
            )
        
        elif status == cp_model.INFEASIBLE:
            reason = self._analyze_infeasibility()
            return ScheduleResult(
                status="infeasible",
                items=[],
                solver_wall_time_ms=wall_time_ms,
                objective_value=None,
                objective_breakdown=None,
                infeasible_reason=reason,
            )
        
        else:
            return ScheduleResult(
                status="failed",
                items=[],
                solver_wall_time_ms=wall_time_ms,
                objective_value=None,
                objective_breakdown=None,
                infeasible_reason=f"Solver status: {solver.StatusName(status)}",
            )
    
    def _extract_solution(self, solver: cp_model.CpSolver) -> list[ScheduleItem]:
        """Extract schedule items from solution."""
        items = []
        
        # Add unlocked tasks
        for task in self.input.get_unlocked_tasks():
            start_minutes = solver.Value(self.task_starts[task.id])
            end_minutes = solver.Value(self.task_ends[task.id])
            tech_index = solver.Value(self.task_tech_assignments[task.id])
            bay_index = solver.Value(self.task_bay_assignments[task.id])
            
            tech_id = self.input.technicians[tech_index].id
            bay_id = self.input.bays[bay_index].id
            
            items.append(ScheduleItem(
                task_id=task.id,
                technician_id=tech_id,
                bay_id=bay_id,
                start_at=minutes_to_datetime(start_minutes, self.input.horizon_start),
                end_at=minutes_to_datetime(end_minutes, self.input.horizon_start),
                is_locked=False,
                why={"reason": "optimized"},
            ))
        
        # Add locked tasks
        for task in self.input.get_locked_tasks():
            items.append(ScheduleItem(
                task_id=task.id,
                technician_id=task.locked_tech_id,
                bay_id=task.locked_bay_id,
                start_at=task.locked_start_at,
                end_at=task.locked_end_at,
                is_locked=True,
                why={"reason": "locked"},
            ))
        
        return items
    
    def _calculate_objective_breakdown(self, solver: cp_model.CpSolver) -> ObjectiveBreakdown:
        """Calculate breakdown of objective components."""
        due_date_penalty = 0
        priority_penalty = 0
        skill_mismatch_penalty = 0
        parts_not_ready_penalty = 0
        
        for key, var in self.penalty_vars.items():
            value = solver.Value(var)
            
            if key.startswith("due_date_"):
                due_date_penalty += value
            elif key.startswith("priority_"):
                priority_penalty += value
            elif key.startswith("skill_mismatch_"):
                skill_mismatch_penalty += value
            elif key.startswith("parts_not_ready_"):
                parts_not_ready_penalty += value
        
        total = due_date_penalty + priority_penalty + skill_mismatch_penalty + parts_not_ready_penalty
        
        return ObjectiveBreakdown(
            total_penalty=total,
            due_date_penalty=due_date_penalty,
            priority_penalty=priority_penalty,
            skill_mismatch_penalty=skill_mismatch_penalty,
            parts_not_ready_penalty=parts_not_ready_penalty,
        )
    
    def _analyze_infeasibility(self) -> str:
        """Analyze why model is infeasible."""
        reasons = []
        
        # Check for impossible skill requirements
        for task in self.input.get_unlocked_tasks():
            if task.required_skill and task.required_skill_is_hard:
                techs_with_skill = [
                    t for t in self.input.technicians
                    if task.required_skill in t.skills
                ]
                if not techs_with_skill:
                    reasons.append(
                        f"Task {task.id} requires skill '{task.required_skill}' "
                        f"but no technician has it"
                    )
        
        # Check for impossible bay requirements
        for task in self.input.get_unlocked_tasks():
            if task.required_bay_type:
                bays_with_type = [
                    b for b in self.input.bays
                    if b.bay_type == task.required_bay_type
                ]
                if not bays_with_type:
                    reasons.append(
                        f"Task {task.id} requires bay type '{task.required_bay_type}' "
                        f"but no bay has it"
                    )
        
        # Check if horizon is too short
        total_duration = sum(t.duration_minutes for t in self.input.get_unlocked_tasks())
        total_capacity = len(self.input.technicians) * self.horizon_minutes
        if total_duration > total_capacity:
            reasons.append(
                f"Total task duration ({total_duration} min) exceeds "
                f"total tech capacity ({total_capacity} min)"
            )
        
        if reasons:
            return "; ".join(reasons)
        else:
            return "Unable to find feasible schedule (constraint conflict)"


def run_scheduler(input_data: ScheduleInput, time_limit_seconds: int = 30) -> ScheduleResult:
    """
    Run the CP-SAT scheduler.
    
    Args:
        input_data: Schedule input data
        time_limit_seconds: Maximum solve time
    
    Returns:
        ScheduleResult with solution
    """
    model = SchedulerModel(input_data)
    model.build()
    return model.solve(time_limit_seconds)
