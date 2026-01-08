# Scheduler v1 (Milestone C)

## Overview

The Woflo scheduler uses Google OR-Tools CP-SAT (Constraint Programming - Satisfiability) solver to create optimal task schedules respecting resource constraints, due dates, skills, and manual overrides.

## Architecture

```
API Request
    ↓
POST /v1/schedules
    ↓
Create schedule_run (status='queued')
    ↓
Enqueue job_queue entry
    ↓
Worker picks up job
    ↓
Load data (tasks, techs, bays, work orders)
    ↓
Build CP-SAT model
    ├── Create task interval variables
    ├── Add no-overlap constraints (tech/bay)
    ├── Add skill constraints
    ├── Add bay type constraints
    ├── Add time window constraints
    ├── Add parts gate constraints
    ├── Handle locked tasks
    └── Create objective function
    ↓
Solve CP-SAT model (max 30s)
    ↓
Extract solution
    ↓
Save schedule_items + update schedule_runs
    ↓
Update task statuses to 'scheduled'
```

## Constraints

### 1. No-Overlap Constraints (Hard)

**Technician No-Overlap**: Each technician can only work on one task at a time.

```python
# For each technician, create optional intervals for assigned tasks
# Locked tasks create fixed intervals
# CP-SAT ensures no overlap via AddNoOverlap()
```

**Bay No-Overlap**: Each bay can only host one task at a time.

```python
# For each bay, create optional intervals for assigned tasks
# Locked tasks create fixed intervals
# CP-SAT ensures no overlap via AddNoOverlap()
```

### 2. Skill Constraints (Hard/Soft)

Tasks may require specific skills:

- **Hard constraint** (`required_skill_is_hard=true`): Task MUST be assigned to a technician with the skill. Model is infeasible if no tech has the skill.
- **Soft constraint** (`required_skill_is_hard=false`): Penalty added if assigned tech doesn't have skill (50 points per mismatch).

```python
# Hard: AddAllowedAssignments() restricts tech to those with skill
# Soft: Penalty variable activated when skill mismatch detected
```

### 3. Bay Type Constraints (Hard)

Tasks requiring a specific bay type (e.g., "heavy_lift") must be assigned to a bay of that type.

```python
# AddAllowedAssignments() restricts bay to those matching required_bay_type
```

### 4. Time Window Constraints (Hard)

Tasks can have time restrictions:

- **Earliest start** (`earliest_start`): Task cannot start before this time
- **Latest finish** (`latest_finish`): Task must finish by this time

```python
# start_var >= earliest_start_minutes
# end_var <= latest_finish_minutes
```

### 5. Parts Gate Constraints (Soft)

Tasks for work orders where `parts_ready=false` get a penalty (100 points).

This encourages the scheduler to defer these tasks, but doesn't prevent scheduling if capacity allows.

```python
# Fixed penalty variable added to objective for tasks with parts not ready
```

### 6. Locked Tasks (Hard)

Manually locked tasks are treated as fixed:

- Locked tasks are NOT rescheduled by the solver
- They create fixed intervals that block tech/bay resources
- Unlocked tasks must work around locked tasks

```python
# Locked tasks: NewFixedSizeIntervalVar() at locked_start_at -> locked_end_at
# Added to no-overlap constraints to prevent conflicts
```

## Objective Function

The scheduler minimizes total penalty, comprised of:

### 1. Due Date Penalty

Tasks finishing after work order due date incur penalty:

```
penalty = priority * 100 (if task_end > due_date)
```

Higher priority work orders get higher penalty for missing due dates.

### 2. Priority Penalty

Earlier start times preferred for higher priority work orders:

```
penalty = task_start * (6 - priority) / 100
```

Priority 5 (highest) tasks are encouraged to start earlier.

### 3. Skill Mismatch Penalty

Assigning task to tech without required skill (soft constraint):

```
penalty = 50 per mismatch
```

### 4. Parts Not Ready Penalty

Scheduling task before parts are ready:

```
penalty = 100 per task
```

### Total Objective

```
minimize(
    Σ due_date_penalties +
    Σ priority_penalties +
    Σ skill_mismatch_penalties +
    Σ parts_not_ready_penalties
)
```

## Performance

**Target**: 50-task scenario solves in ≤10 seconds

**Actual**: Typical scenarios solve in 1-5 seconds. Complex scenarios may take up to 30 seconds (default timeout).

**Factors affecting solve time**:
- Number of tasks (linear to quadratic impact)
- Number of techs/bays (affects variable count)
- Number of locked tasks (reduces search space)
- Tightness of time windows
- Number of hard constraints

## Infeasibility

When no feasible schedule exists, the solver returns `INFEASIBLE` and provides analysis:

**Common causes**:
1. **Impossible skill requirements**: Task requires skill X, but no tech has it
2. **Impossible bay requirements**: Task requires bay type Y, but no bay has it  
3. **Insufficient capacity**: Total task duration exceeds available tech-hours
4. **Time window conflicts**: Locked tasks + time windows create impossible constraints
5. **Over-constrained resources**: Too many tasks competing for limited resources

**Example infeasibility message**:
```
Task abc123 requires skill 'diesel_diagnosis' but no technician has it;
Task def456 requires bay type 'heavy_lift' but no bay has it;
Total task duration (2400 min) exceeds total tech capacity (1920 min)
```

## API Usage

### Create Schedule Run

```bash
POST /v1/schedules
Content-Type: application/json
Authorization: Bearer $TOKEN

{
  "horizon_start": "2026-01-07T00:00:00Z",
  "horizon_end": "2026-01-14T00:00:00Z",
  "trigger": "manual"
}
```

**Response**:
```json
{
  "id": "schedule-run-uuid",
  "status": "queued",
  "job_id": "job-uuid"
}
```

### Get Schedule Run Status

```bash
GET /v1/schedules/{schedule_run_id}
Authorization: Bearer $TOKEN
```

**Response**:
```json
{
  "id": "schedule-run-uuid",
  "status": "succeeded",
  "task_count": 45,
  "solver_wall_time_ms": 3420,
  "objective_value": 1250,
  "objective_breakdown": {
    "total_penalty": 1250,
    "due_date_penalty": 500,
    "priority_penalty": 600,
    "skill_mismatch_penalty": 50,
    "parts_not_ready_penalty": 100
  },
  "horizon_start": "2026-01-07T00:00:00Z",
  "horizon_end": "2026-01-14T00:00:00Z"
}
```

### Get Schedule Items

```bash
GET /v1/schedules/{schedule_run_id}/items
Authorization: Bearer $TOKEN
```

**Response**:
```json
[
  {
    "id": "item-uuid",
    "task_id": "task-uuid",
    "technician_id": "tech-uuid",
    "technician_name": "John Smith",
    "bay_id": "bay-uuid",
    "bay_name": "Bay 1",
    "start_at": "2026-01-07T08:00:00Z",
    "end_at": "2026-01-07T10:30:00Z",
    "is_locked": false,
    "why": {
      "reason": "optimized"
    }
  }
]
```

## Data Model

### Schedule Runs

```sql
schedule_runs
├── id (uuid)
├── org_id (uuid)
├── horizon_start (timestamptz)
├── horizon_end (timestamptz)
├── status (queued|running|succeeded|failed)
├── trigger (manual|auto_parts|auto_callout|auto_hot_job|override)
├── locked_task_count (int)
├── task_count (int)
├── solver_wall_time_ms (int)
├── objective_value (numeric)
├── objective_breakdown (jsonb)
├── solver_status (text)
├── infeasible_reason (text)
└── created_by (uuid)
```

### Schedule Items

```sql
schedule_items
├── id (uuid)
├── schedule_run_id (uuid)
├── task_id (uuid)
├── technician_id (uuid)
├── bay_id (uuid)
├── start_at (timestamptz)
├── end_at (timestamptz)
├── is_locked (boolean)
└── why (jsonb) -- explainability payload
```

## Locked Tasks

Dispatchers can manually lock tasks to override the scheduler:

```sql
update tasks
set
  lock_flag = true,
  locked_tech_id = 'tech-uuid',
  locked_bay_id = 'bay-uuid',
  locked_start_at = '2026-01-07 08:00:00',
  locked_end_at = '2026-01-07 10:00:00'
where id = 'task-uuid';
```

Locked tasks:
- Are NOT moved by the scheduler
- Block their assigned tech/bay during locked time window
- Appear in schedule with `is_locked=true`
- Have `why.reason = "locked"`

## Explainability

Each schedule item includes a `why` field explaining the assignment:

```json
{
  "reason": "optimized",
  "penalty_contributions": {
    "due_date": 0,
    "priority": 15,
    "skill_mismatch": 0,
    "parts_not_ready": 0
  }
}
```

For locked tasks:
```json
{
  "reason": "locked"
}
```

## Monitoring

### Check Schedule Run Performance

```sql
select
  status,
  avg(solver_wall_time_ms) as avg_solve_time_ms,
  avg(task_count) as avg_tasks,
  count(*) as run_count
from schedule_runs
where created_at > now() - interval '7 days'
group by status;
```

### Find Infeasible Runs

```sql
select
  id,
  task_count,
  locked_task_count,
  infeasible_reason,
  created_at
from schedule_runs
where status = 'failed'
  and solver_status = 'INFEASIBLE'
order by created_at desc
limit 10;
```

### Objective Breakdown Analysis

```sql
select
  id,
  task_count,
  objective_value,
  (objective_breakdown->>'due_date_penalty')::int as due_date_penalty,
  (objective_breakdown->>'priority_penalty')::int as priority_penalty,
  (objective_breakdown->>'skill_mismatch_penalty')::int as skill_mismatch,
  (objective_breakdown->>'parts_not_ready_penalty')::int as parts_not_ready
from schedule_runs
where status = 'succeeded'
  and created_at > now() - interval '7 days'
order by objective_value desc
limit 10;
```

## Testing

### Create Test Data

```sql
-- Create test tasks
insert into tasks (org_id, work_order_id, type, status, duration_minutes_low, duration_minutes_high)
select
  'org-uuid',
  'wo-uuid',
  'repair',
  'todo',
  60,
  120
from generate_series(1, 50);
```

### Run Schedule

```bash
curl -X POST http://localhost:8000/v1/schedules \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "horizon_start": "2026-01-07T00:00:00Z",
    "horizon_end": "2026-01-14T00:00:00Z"
  }'
```

### Verify Results

```sql
-- Check schedule items
select
  t.name as technician,
  count(*) as task_count,
  sum(extract(epoch from (si.end_at - si.start_at))/60) as total_minutes
from schedule_items si
join technicians t on t.id = si.technician_id
where si.schedule_run_id = 'schedule-run-uuid'
group by t.name
order by task_count desc;
```

## Future Enhancements (Post-MVP)

### Dependencies (Task Ordering)
Add precedence constraints so tasks can depend on completion of other tasks.

### Multi-Skill Requirements
Support tasks requiring multiple skills (e.g., diesel + electrical).

### Travel Time
Account for travel time between field jobs.

### Shift Constraints
Respect technician shift hours and breaks.

### Warm Start
Use previous schedule as starting point for faster reoptimization.

### Partial Reoptimization
Only reschedule tasks affected by changes, keeping others fixed.

## Troubleshooting

### Slow Solve Times (>30s)

1. **Reduce time horizon**: Shorter horizons = fewer variables
2. **Lock more tasks**: Locked tasks reduce search space
3. **Simplify constraints**: Remove soft constraints if not critical
4. **Increase time limit**: Set `time_limit_seconds` higher in payload

### Frequent Infeasibility

1. **Check resource availability**: Ensure enough techs/bays for workload
2. **Review hard constraints**: Are skill/bay requirements too restrictive?
3. **Adjust time windows**: Are earliest_start/latest_finish too tight?
4. **Unlock some tasks**: Too many locks can over-constrain

### Poor Schedule Quality

1. **Check objective weights**: Adjust penalty values in cp_sat_scheduler.py
2. **Review locked tasks**: Manual locks may prevent better solutions
3. **Verify task durations**: Inaccurate estimates lead to suboptimal packing
4. **Add more resources**: More techs/bays = more optimization opportunities

## References

- [OR-Tools CP-SAT Documentation](https://developers.google.com/optimization/cp/cp_solver)
- [Job Shop Scheduling Example](https://developers.google.com/optimization/scheduling/job_shop)
- [Employee Scheduling Example](https://developers.google.com/optimization/scheduling/employee_scheduling)
