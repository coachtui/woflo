import Link from 'next/link';
import Image from 'next/image';
import { Calendar, ClipboardList, CheckSquare, Play } from 'lucide-react';

export default function Home() {
  return (
    <div className="min-h-screen bg-white">
      {/* Header */}
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto max-w-7xl px-4 py-2">
          <Image 
            src="/aiga-logo.png" 
            alt="Woflo" 
            width={180} 
            height={54}
            className="h-8 w-auto"
            priority
          />
        </div>
      </header>

      {/* Hero Section */}
      <div className="mx-auto max-w-7xl px-6 py-12">
        <div className="text-center mb-12">
          {/* Large centered logo */}
          <div className="flex flex-col items-center">
          <Image 
            src="/woflo-black.png" 
            alt="Woflo" 
            width={1000} 
            height={600}
            className="h-120 w-auto"
            priority
          />      
  <h1 className="mx-auto mt-5 text-5xl font-bold text-slate-900 tracking-tight overflow-hidden">
    AI-Powered Scheduling &<br />Workflow Management
  </h1>
</div>

          <p className="text-xl text-slate-600 max-w-2xl mx-auto">
            Optimize your diesel shop operations with intelligent constraint-based scheduling
          </p>
        </div>

        {/* Main Cards */}
        <div className="grid md:grid-cols-3 gap-6 mb-10">
          <Link 
            href="/schedule"
            className="group p-8 bg-white border-2 border-slate-200 rounded-xl shadow-sm hover:shadow-lg hover:border-aiga-yellow transition-all"
          >
            <div className="flex items-center gap-3 mb-4">
              <div className="p-2 bg-slate-100 rounded-lg group-hover:bg-aiga-yellow/10 transition-colors">
                <Calendar className="h-6 w-6 text-slate-700 group-hover:text-aiga-gold" />
              </div>
              <h2 className="text-xl font-bold text-slate-900">
                Schedule Board
              </h2>
            </div>
            <p className="text-slate-600 leading-relaxed">
              AI-optimized technician schedules with resource allocation
            </p>
          </Link>

          <Link 
            href="/work-orders"
            className="group p-8 bg-white border-2 border-slate-200 rounded-xl shadow-sm hover:shadow-lg hover:border-aiga-yellow transition-all"
          >
            <div className="flex items-center gap-3 mb-4">
              <div className="p-2 bg-slate-100 rounded-lg group-hover:bg-aiga-yellow/10 transition-colors">
                <ClipboardList className="h-6 w-6 text-slate-700 group-hover:text-aiga-gold" />
              </div>
              <h2 className="text-xl font-bold text-slate-900">
                Work Orders
              </h2>
            </div>
            <p className="text-slate-600 leading-relaxed">
              Manage queue, priorities and track progress
            </p>
          </Link>

          <Link 
            href="/tasks"
            className="group p-8 bg-white border-2 border-slate-200 rounded-xl shadow-sm hover:shadow-lg hover:border-aiga-yellow transition-all"
          >
            <div className="flex items-center gap-3 mb-4">
              <div className="p-2 bg-slate-100 rounded-lg group-hover:bg-aiga-yellow/10 transition-colors">
                <CheckSquare className="h-6 w-6 text-slate-700 group-hover:text-aiga-gold" />
              </div>
              <h2 className="text-xl font-bold text-slate-900">
                Tasks
              </h2>
            </div>
            <p className="text-slate-600 leading-relaxed">
              View assignments, skills and bay requirements
            </p>
          </Link>
        </div>

        {/* Quick Actions */}
        <div className="bg-slate-50 border border-slate-200 rounded-xl p-8 mb-10">
          <h3 className="text-lg font-bold text-slate-900 mb-6 flex items-center gap-2">
            <Play className="h-5 w-5 text-aiga-gold" />
            Quick Actions
          </h3>
          <div className="flex flex-wrap gap-3">
            <Link 
              href="/schedule"
              className="px-6 py-3 bg-aiga-yellow text-slate-900 rounded-lg hover:bg-aiga-gold font-semibold transition-colors shadow-sm"
            >
              New Schedule Run
            </Link>
            <Link 
              href="/work-orders"
              className="px-6 py-3 bg-white border-2 border-slate-200 text-slate-900 rounded-lg hover:border-aiga-yellow font-semibold transition-colors"
            >
              Browse Work Orders
            </Link>
            <Link 
              href="/tasks"
              className="px-6 py-3 bg-white border-2 border-slate-200 text-slate-900 rounded-lg hover:border-aiga-yellow font-semibold transition-colors"
            >
              View All Tasks
            </Link>
          </div>
        </div>
      </div>

      {/* Footer */}
      <footer className="border-t border-slate-200 bg-white mt-auto">
        <div className="mx-auto max-w-7xl px-6 py-6 text-center">
          <p className="text-sm text-slate-600 mb-1">
            Powered by <span className="font-semibold text-slate-900">AIGA</span>
          </p>
          <p className="text-xs text-slate-500">
            AI-Driven Workflow Optimization
          </p>
        </div>
      </footer>
    </div>
  );
}
