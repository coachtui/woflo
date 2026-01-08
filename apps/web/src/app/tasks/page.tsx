'use client';

import { useEffect, useState } from 'react';
import { CheckSquare, Clock, PlayCircle, CheckCircle2, Lock } from 'lucide-react';
import { api } from '@/lib/api';
import { PageShell } from '@/components/layout/page-shell';
import { Card, StatCard, CardHeader } from '@/components/ui/card';
import { Badge, StatusBadge } from '@/components/ui/badge';
import { LoadingState, EmptyState } from '@/components/ui/states';
import { formatDate, formatDuration } from '@/lib/utils';

export default function TasksPage() {
  const [tasks, setTasks] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadTasks();
  }, []);

  const loadTasks = async () => {
    try {
      const data = await api.listTasks();
      setTasks(data);
    } catch (error) {
      console.error('Failed to load tasks:', error);
    } finally {
      setLoading(false);
    }
  };

  const tasksByStatus = {
    todo: tasks.filter((t) => t.status === 'todo'),
    scheduled: tasks.filter((t) => t.status === 'scheduled'),
    in_progress: tasks.filter((t) => t.status === 'in_progress'),
    completed: tasks.filter((t) => t.status === 'completed'),
  };

  const getTypeVariant = (type: string): 'danger' | 'info' | 'warning' | 'default' => {
    switch (type) {
      case 'repair':
        return 'danger';
      case 'pm':
        return 'info';
      case 'inspection':
        return 'warning';
      default:
        return 'default';
    }
  };

  return (
    <PageShell
      title="Tasks"
      description="View and manage all maintenance and repair tasks"
    >
      {loading ? (
        <LoadingState message="Loading tasks..." />
      ) : (
        <>
          {/* Stats */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
            <StatCard
              label="To Do"
              value={tasksByStatus.todo.length}
              icon={<CheckSquare className="h-5 w-5" />}
            />
            <StatCard
              label="Scheduled"
              value={tasksByStatus.scheduled.length}
              icon={<Clock className="h-5 w-5 text-purple-600" />}
            />
            <StatCard
              label="In Progress"
              value={tasksByStatus.in_progress.length}
              icon={<PlayCircle className="h-5 w-5 text-blue-600" />}
            />
            <StatCard
              label="Completed"
              value={tasksByStatus.completed.length}
              icon={<CheckCircle2 className="h-5 w-5 text-emerald-600" />}
            />
          </div>

          {/* Tasks */}
          {tasks.length === 0 ? (
            <Card>
              <EmptyState
                icon={<CheckSquare className="h-6 w-6 text-slate-400" />}
                title="No tasks found"
                description="Tasks will appear here when work orders are created"
              />
            </Card>
          ) : (
            <div className="space-y-8">
              {Object.entries(tasksByStatus).map(
                ([status, statusTasks]) =>
                  statusTasks.length > 0 && (
                    <div key={status}>
                      <h2 className="text-xl font-semibold capitalize mb-4 text-slate-900">
                        {status.replace('_', ' ')} ({statusTasks.length})
                      </h2>
                      <div className="space-y-3">
                        {statusTasks.map((task) => (
                          <Card key={task.id} className="hover:shadow-card-hover transition-shadow">
                            <div className="flex items-start justify-between">
                              <div className="flex-1">
                                <div className="flex items-center gap-2 mb-3">
                                  <h3 className="text-base font-semibold text-slate-900">
                                    #{task.id.substring(0, 8)}
                                  </h3>
                                  <Badge variant={getTypeVariant(task.type)} size="sm">
                                    {task.type.toUpperCase()}
                                  </Badge>
                                  <StatusBadge status={task.status} />
                                  {task.lock_flag && (
                                    <Badge variant="warning" size="sm">
                                      <Lock className="h-3 w-3 mr-1" />
                                      Locked
                                    </Badge>
                                  )}
                                </div>

                                <div className="grid grid-cols-3 gap-6 text-sm">
                                  <div>
                                    <p className="text-slate-600">
                                      <span className="font-medium text-slate-900">WO:</span>{' '}
                                      {task.work_order_id.substring(0, 8)}
                                    </p>
                                    {task.required_skill && (
                                      <p className="text-slate-600 mt-1">
                                        <span className="font-medium text-slate-900">Skill:</span>{' '}
                                        {task.required_skill}
                                        {task.required_skill_is_hard && ' (hard)'}
                                      </p>
                                    )}
                                  </div>
                                  <div>
                                    <p className="text-slate-600">
                                      <span className="font-medium text-slate-900">Duration:</span>{' '}
                                      {formatDuration(task.duration_minutes_low)}-
                                      {formatDuration(task.duration_minutes_high)}
                                    </p>
                                    {task.required_bay_type && (
                                      <p className="text-slate-600 mt-1">
                                        <span className="font-medium text-slate-900">Bay:</span>{' '}
                                        {task.required_bay_type}
                                      </p>
                                    )}
                                  </div>
                                  <div>
                                    {task.earliest_start && (
                                      <p className="text-slate-600">
                                        <span className="font-medium text-slate-900">Earliest:</span>{' '}
                                        {formatDate(task.earliest_start)}
                                      </p>
                                    )}
                                    {task.latest_finish && (
                                      <p className="text-slate-600 mt-1">
                                        <span className="font-medium text-slate-900">Latest:</span>{' '}
                                        {formatDate(task.latest_finish)}
                                      </p>
                                    )}
                                  </div>
                                </div>
                              </div>

                              <div className="ml-4 flex gap-2">
                                <button className="px-3 py-1.5 text-sm font-medium text-slate-700 bg-slate-100 hover:bg-slate-200 rounded-md transition-colors">
                                  View
                                </button>
                              </div>
                            </div>
                          </Card>
                        ))}
                      </div>
                    </div>
                  )
              )}
            </div>
          )}

          {/* Info Card */}
          <Card className="mt-8 bg-slate-50 border-slate-300">
            <CardHeader
              title="Task Management"
              description="How tasks are organized and scheduled"
            />
            <ul className="text-sm text-slate-700 space-y-2">
              <li className="flex items-start">
                <CheckCircle2 className="h-4 w-4 text-aiga-gold mr-2 mt-0.5 flex-shrink-0" />
                Tasks are auto-generated from work orders
              </li>
              <li className="flex items-start">
                <Lock className="h-4 w-4 text-aiga-gold mr-2 mt-0.5 flex-shrink-0" />
                Locked tasks respect manual dispatcher assignments
              </li>
              <li className="flex items-start">
                <PlayCircle className="h-4 w-4 text-aiga-gold mr-2 mt-0.5 flex-shrink-0" />
                Scheduler optimizes todo/scheduled tasks automatically
              </li>
              <li className="flex items-start">
                <CheckSquare className="h-4 w-4 text-aiga-gold mr-2 mt-0.5 flex-shrink-0" />
                Skills and bay types ensure proper resource matching
              </li>
            </ul>
          </Card>
        </>
      )}
    </PageShell>
  );
}
