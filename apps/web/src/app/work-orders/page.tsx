'use client';

import { useEffect, useState } from 'react';
import { ClipboardList, AlertCircle, Package, TrendingUp } from 'lucide-react';
import { api } from '@/lib/api';
import { PageShell } from '@/components/layout/page-shell';
import { Card, StatCard } from '@/components/ui/card';
import { Badge, PriorityBadge, StatusBadge } from '@/components/ui/badge';
import { LoadingState, EmptyState } from '@/components/ui/states';
import { formatDate } from '@/lib/utils';
import { cn } from '@/lib/utils';

export default function WorkOrdersPage() {
  const [workOrders, setWorkOrders] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<string>('all');

  useEffect(() => {
    loadWorkOrders();
  }, [filter]);

  const loadWorkOrders = async () => {
    try {
      const statusFilter = filter !== 'all' ? filter : undefined;
      const data = await api.listWorkOrders(statusFilter);
      setWorkOrders(data);
    } catch (error) {
      console.error('Failed to load work orders:', error);
    } finally {
      setLoading(false);
    }
  };

  const stats = {
    total: workOrders.length,
    highPriority: workOrders.filter((wo) => wo.priority >= 4).length,
    partsReady: workOrders.filter((wo) => wo.parts_ready).length,
    inProgress: workOrders.filter((wo) => wo.status === 'in_progress').length,
  };

  return (
    <PageShell
      title="Work Orders"
      description="Manage repair and maintenance work orders"
    >
      {loading ? (
        <LoadingState message="Loading work orders..." />
      ) : (
        <>
          {/* Stats */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
            <StatCard
              label="Total Work Orders"
              value={stats.total}
              icon={<ClipboardList className="h-5 w-5" />}
            />
            <StatCard
              label="High Priority"
              value={stats.highPriority}
              icon={<AlertCircle className="h-5 w-5 text-red-600" />}
            />
            <StatCard
              label="Parts Ready"
              value={stats.partsReady}
              icon={<Package className="h-5 w-5 text-emerald-600" />}
            />
            <StatCard
              label="In Progress"
              value={stats.inProgress}
              icon={<TrendingUp className="h-5 w-5 text-blue-600" />}
            />
          </div>

          {/* Filters */}
          <Card className="mb-6">
            <div className="flex gap-2">
              {[
                { key: 'all', label: 'All' },
                { key: 'todo', label: 'To Do' },
                { key: 'in_progress', label: 'In Progress' },
                { key: 'completed', label: 'Completed' },
              ].map((status) => (
                <button
                  key={status.key}
                  onClick={() => setFilter(status.key)}
                  className={cn(
                    'px-4 py-2 text-sm font-medium rounded-md transition-colors',
                    filter === status.key
                      ? 'bg-aiga-yellow text-aiga-black'
                      : 'bg-slate-100 text-slate-700 hover:bg-slate-200'
                  )}
                >
                  {status.label}
                </button>
              ))}
            </div>
          </Card>

          {/* Work Orders */}
          {workOrders.length === 0 ? (
            <Card>
              <EmptyState
                icon={<ClipboardList className="h-6 w-6 text-slate-400" />}
                title="No work orders found"
                description={
                  filter !== 'all'
                    ? `No work orders with status "${filter.replace('_', ' ')}"`
                    : 'Create work orders to get started'
                }
              />
            </Card>
          ) : (
            <div className="space-y-4">
              {workOrders.map((wo) => (
                <Card key={wo.id} className="hover:shadow-card-hover transition-shadow">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-3">
                        <h3 className="text-base font-semibold text-slate-900">
                          WO-{wo.id.substring(0, 8)}
                        </h3>
                        <PriorityBadge priority={wo.priority} />
                        <StatusBadge status={wo.status} />
                        {wo.parts_ready && (
                          <Badge variant="success" size="sm">
                            <Package className="h-3 w-3 mr-1" />
                            Parts Ready
                          </Badge>
                        )}
                      </div>

                      <div className="grid grid-cols-3 gap-6 text-sm">
                        <div>
                          <p className="text-slate-600">
                            <span className="font-medium text-slate-900">Unit:</span>{' '}
                            {wo.unit_id.substring(0, 12)}
                          </p>
                        </div>
                        <div>
                          <p className="text-slate-600">
                            <span className="font-medium text-slate-900">Type:</span>{' '}
                            {wo.asset_type}
                          </p>
                        </div>
                        {wo.due_date && (
                          <div>
                            <p className="text-slate-600">
                              <span className="font-medium text-slate-900">Due:</span>{' '}
                              {formatDate(wo.due_date)}
                            </p>
                          </div>
                        )}
                      </div>
                    </div>

                    <div className="ml-4 flex gap-2">
                      <button className="px-3 py-1.5 text-sm font-medium text-slate-700 bg-slate-100 hover:bg-slate-200 rounded-md transition-colors">
                        View
                      </button>
                      <button className="px-3 py-1.5 text-sm font-medium text-slate-700 bg-slate-100 hover:bg-slate-200 rounded-md transition-colors">
                        Edit
                      </button>
                    </div>
                  </div>
                </Card>
              ))}
            </div>
          )}
        </>
      )}
    </PageShell>
  );
}
