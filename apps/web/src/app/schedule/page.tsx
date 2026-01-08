'use client';

import { useEffect, useState } from 'react';
import { Play, Clock, CheckCircle2, XCircle, Calendar } from 'lucide-react';
import { api } from '@/lib/api';
import { PageShell } from '@/components/layout/page-shell';
import { Card, CardHeader, StatCard } from '@/components/ui/card';
import { Badge, StatusBadge } from '@/components/ui/badge';
import { LoadingState, EmptyState } from '@/components/ui/states';
import { formatDate } from '@/lib/utils';

export default function SchedulePage() {
  const [schedules, setSchedules] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState(false);

  useEffect(() => {
    loadSchedules();
  }, []);

  const loadSchedules = async () => {
    try {
      const data = await api.listSchedules();
      setSchedules(data);
    } catch (error) {
      console.error('Failed to load schedules:', error);
    } finally {
      setLoading(false);
    }
  };

  const createSchedule = async () => {
    setCreating(true);
    try {
      const now = new Date();
      const weekFromNow = new Date(now.getTime() + 7 * 24 * 60 * 60 * 1000);
      
      await api.createSchedule({
        horizon_start: now.toISOString(),
        horizon_end: weekFromNow.toISOString(),
      });
      
      await loadSchedules();
    } catch (error) {
      console.error('Failed to create schedule:', error);
      alert('Failed to create schedule. Make sure you have a valid auth token.');
    } finally {
      setCreating(false);
    }
  };

  const succeeded = schedules.filter((s) => s.status === 'succeeded').length;
  const failed = schedules.filter((s) => s.status === 'failed').length;
  const running = schedules.filter((s) => s.status === 'running').length;

  return (
    <PageShell
      title="Schedule Board"
      description="AI-optimized schedules using OR-Tools CP-SAT constraint solver"
      actions={
        <button
          onClick={createSchedule}
          disabled={creating}
          className="inline-flex items-center px-4 py-2 bg-aiga-yellow text-aiga-black text-sm font-semibold rounded-md hover:bg-aiga-gold disabled:opacity-50 transition-colors"
        >
          <Play className="h-4 w-4 mr-2" />
          {creating ? 'Creating...' : 'New Schedule Run'}
        </button>
      }
    >
      {loading ? (
        <LoadingState message="Loading schedule runs..." />
      ) : (
        <>
          {/* Stats */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
            <StatCard
              label="Total Runs"
              value={schedules.length}
              icon={<Calendar className="h-5 w-5" />}
            />
            <StatCard
              label="Succeeded"
              value={succeeded}
              icon={<CheckCircle2 className="h-5 w-5 text-emerald-600" />}
            />
            <StatCard
              label="Running"
              value={running}
              icon={<Clock className="h-5 w-5 text-blue-600" />}
            />
            <StatCard
              label="Failed"
              value={failed}
              icon={<XCircle className="h-5 w-5 text-red-600" />}
            />
          </div>

          {/* Schedule Runs */}
          {schedules.length === 0 ? (
            <Card>
              <EmptyState
                icon={<Calendar className="h-6 w-6 text-slate-400" />}
                title="No schedule runs yet"
                description="Create your first schedule run to see the AI optimizer in action"
                action={
                  <button
                    onClick={createSchedule}
                    disabled={creating}
                    className="px-4 py-2 bg-aiga-yellow text-aiga-black text-sm font-semibold rounded-md hover:bg-aiga-gold transition-colors"
                  >
                    Create First Schedule
                  </button>
                }
              />
            </Card>
          ) : (
            <div className="space-y-4">
              {schedules.map((schedule) => (
                <Card key={schedule.id} className="hover:shadow-card-hover transition-shadow">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-3 mb-3">
                        <h3 className="text-base font-semibold text-slate-900">
                          Run #{schedule.id.substring(0, 8)}
                        </h3>
                        <StatusBadge status={schedule.status} />
                        {schedule.task_count && (
                          <Badge variant="default">{schedule.task_count} tasks</Badge>
                        )}
                      </div>
                      
                      <div className="grid grid-cols-2 gap-4 text-sm">
                        <div>
                          <p className="text-slate-600">
                            <span className="font-medium text-slate-900">Period:</span>{' '}
                            {formatDate(schedule.horizon_start)} → {formatDate(schedule.horizon_end)}
                          </p>
                        </div>
                        {schedule.solver_wall_time_ms && (
                          <div>
                            <p className="text-slate-600">
                              <span className="font-medium text-slate-900">Solve Time:</span>{' '}
                              {(schedule.solver_wall_time_ms / 1000).toFixed(2)}s
                            </p>
                          </div>
                        )}
                      </div>
                    </div>

                    {schedule.objective_value !== null && (
                      <div className="ml-6 text-right">
                        <p className="text-sm text-slate-600 mb-1">Objective Score</p>
                        <p className="text-2xl font-bold text-slate-900">
                          {schedule.objective_value}
                        </p>
                        {schedule.objective_breakdown && (
                          <div className="mt-2 text-xs text-slate-500 space-y-0.5">
                            <p>Due: {schedule.objective_breakdown.due_date_penalty}</p>
                            <p>Priority: {schedule.objective_breakdown.priority_penalty}</p>
                            <p>Skills: {schedule.objective_breakdown.skill_mismatch_penalty}</p>
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                </Card>
              ))}
            </div>
          )}

          {/* Info Card */}
          <Card className="mt-8 bg-slate-50 border-slate-300">
            <CardHeader
              title="How it Works"
              description="OR-Tools CP-SAT constraint-based optimization"
            />
            <ul className="text-sm text-slate-700 space-y-2">
              <li className="flex items-start">
                <CheckCircle2 className="h-4 w-4 text-aiga-gold mr-2 mt-0.5 flex-shrink-0" />
                Respects technician skills, bay types, and time windows
              </li>
              <li className="flex items-start">
                <CheckCircle2 className="h-4 w-4 text-aiga-gold mr-2 mt-0.5 flex-shrink-0" />
                Honors manually locked tasks (manual overrides)
              </li>
              <li className="flex items-start">
                <CheckCircle2 className="h-4 w-4 text-aiga-gold mr-2 mt-0.5 flex-shrink-0" />
                Optimizes for due dates, priorities, and resource utilization
              </li>
              <li className="flex items-start">
                <CheckCircle2 className="h-4 w-4 text-aiga-gold mr-2 mt-0.5 flex-shrink-0" />
                Typical solve time: &lt;10 seconds for 50 tasks
              </li>
            </ul>
          </Card>
        </>
      )}
    </PageShell>
  );
}
