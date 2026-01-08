import { ReactNode } from 'react';
import { cn } from '@/lib/utils';
import Image from 'next/image';
import Link from 'next/link';

interface PageShellProps {
  children: ReactNode;
  title?: string;
  description?: string;
  actions?: ReactNode;
  className?: string;
  maxWidth?: 'default' | 'wide' | 'full';
}

export function PageShell({
  children,
  title,
  description,
  actions,
  className,
  maxWidth = 'default',
}: PageShellProps) {
  const maxWidthClasses = {
    default: 'max-w-7xl',
    wide: 'max-w-8xl',
    full: 'max-w-none',
  };

  return (
    <div className="min-h-screen bg-slate-50">
      {/* Header */}
      <header className="sticky top-0 z-40 border-b border-slate-200 bg-white/95 backdrop-blur supports-[backdrop-filter]:bg-white/60">
        <div className="mx-auto max-w-8xl px-6">
          <div className="flex h-16 items-center justify-between">
            <Link href="/" className="flex items-center space-x-3">
              <Image
                src="/aiga-logo.png"
                alt="AIGA"
                width={120}
                height={36}
                className="h-9 w-auto"
                priority
              />
            </Link>
            <nav className="flex items-center space-x-1">
              <Link
                href="/schedule"
                className="px-3 py-2 text-sm font-medium text-slate-700 hover:text-slate-900 hover:bg-slate-100 rounded-md transition-colors"
              >
                Schedule
              </Link>
              <Link
                href="/work-orders"
                className="px-3 py-2 text-sm font-medium text-slate-700 hover:text-slate-900 hover:bg-slate-100 rounded-md transition-colors"
              >
                Work Orders
              </Link>
              <Link
                href="/tasks"
                className="px-3 py-2 text-sm font-medium text-slate-700 hover:text-slate-900 hover:bg-slate-100 rounded-md transition-colors"
              >
                Tasks
              </Link>
            </nav>
          </div>
        </div>
      </header>

      {/* Main content */}
      <main className={cn('mx-auto px-6 py-8', maxWidthClasses[maxWidth], className)}>
        {(title || actions) && (
          <div className="mb-8 flex items-start justify-between">
            <div>
              {title && (
                <h1 className="text-3xl font-bold tracking-tight text-slate-900">
                  {title}
                </h1>
              )}
              {description && (
                <p className="mt-2 text-slate-600">{description}</p>
              )}
            </div>
            {actions && <div className="ml-4">{actions}</div>}
          </div>
        )}
        {children}
      </main>
    </div>
  );
}
