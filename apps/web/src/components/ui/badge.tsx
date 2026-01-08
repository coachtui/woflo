import { cva, type VariantProps } from 'class-variance-authority';
import { cn } from '@/lib/utils';

const badgeVariants = cva(
  'inline-flex items-center rounded-md px-2.5 py-0.5 text-xs font-medium transition-colors',
  {
    variants: {
      variant: {
        default: 'bg-slate-100 text-slate-800',
        success: 'bg-emerald-100 text-emerald-800',
        warning: 'bg-amber-100 text-amber-800',
        danger: 'bg-red-100 text-red-800',
        info: 'bg-blue-100 text-blue-800',
        purple: 'bg-purple-100 text-purple-800',
        aiga: 'bg-aiga-yellow text-aiga-black font-semibold',
      },
      size: {
        sm: 'text-xs px-2 py-0.5',
        md: 'text-sm px-2.5 py-0.5',
        lg: 'text-sm px-3 py-1',
      },
    },
    defaultVariants: {
      variant: 'default',
      size: 'md',
    },
  }
);

export interface BadgeProps
  extends React.HTMLAttributes<HTMLSpanElement>,
    VariantProps<typeof badgeVariants> {}

export function Badge({ className, variant, size, ...props }: BadgeProps) {
  return (
    <span className={cn(badgeVariants({ variant, size }), className)} {...props} />
  );
}

// Utility badges for common use cases
export function PriorityBadge({ priority }: { priority: number }) {
  if (priority >= 4) {
    return <Badge variant="danger">P{priority} - High</Badge>;
  }
  if (priority >= 3) {
    return <Badge variant="warning">P{priority} - Medium</Badge>;
  }
  return <Badge variant="info">P{priority} - Normal</Badge>;
}

export function StatusBadge({ status }: { status: string }) {
  const variants: Record<string, 'success' | 'warning' | 'danger' | 'info' | 'default' | 'purple'> = {
    completed: 'success',
    succeeded: 'success',
    in_progress: 'info',
    running: 'info',
    scheduled: 'purple',
    todo: 'default',
    failed: 'danger',
    blocked: 'danger',
  };
  
  return (
    <Badge variant={variants[status] || 'default'}>
      {status.replace('_', ' ')}
    </Badge>
  );
}
