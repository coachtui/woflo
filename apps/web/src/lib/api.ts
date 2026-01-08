// API client for Woflo backend

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export interface Schedule {
  id: string;
  status: string;
  task_count: number;
  solver_wall_time_ms: number;
  objective_value: number;
  horizon_start: string;
  horizon_end: string;
}

export interface ScheduleItem {
  id: string;
  task_id: string;
  technician_id: string;
  technician_name: string;
  bay_id: string;
  bay_name: string;
  start_at: string;
  end_at: string;
  is_locked: boolean;
}

export interface WorkOrder {
  id: string;
  unit_id: string;
  priority: number;
  status: string;
  due_date?: string;
  asset_type: string;
}

class ApiClient {
  private token: string | null = null;

  setToken(token: string) {
    this.token = token;
  }

  private async fetch(endpoint: string, options: RequestInit = {}) {
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      ...(options.headers as Record<string, string>),
    };

    if (this.token) {
      headers['Authorization'] = `Bearer ${this.token}`;
    }

    const response = await fetch(`${API_URL}${endpoint}`, {
      ...options,
      headers,
    });

    if (!response.ok) {
      throw new Error(`API error: ${response.statusText}`);
    }

    return response.json();
  }

  // Schedules
  async createSchedule(data: {
    horizon_start: string;
    horizon_end: string;
  }) {
    return this.fetch('/v1/schedules', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async getSchedule(id: string): Promise<Schedule> {
    return this.fetch(`/v1/schedules/${id}`);
  }

  async listSchedules(): Promise<Schedule[]> {
    return this.fetch('/v1/schedules');
  }

  async getScheduleItems(scheduleId: string): Promise<ScheduleItem[]> {
    return this.fetch(`/v1/schedules/${scheduleId}/items`);
  }

  // Work Orders
  async listWorkOrders(status?: string): Promise<WorkOrder[]> {
    const params = status ? `?status=${status}` : '';
    return this.fetch(`/v1/work-orders${params}`);
  }

  async createWorkOrder(data: Partial<WorkOrder>) {
    return this.fetch('/v1/work-orders', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  // Tasks
  async listTasks() {
    return this.fetch('/v1/tasks');
  }

  async updateTask(id: string, data: any) {
    return this.fetch(`/v1/tasks/${id}`, {
      method: 'PATCH',
      body: JSON.stringify(data),
    });
  }

  // Jobs
  async listJobs() {
    return this.fetch('/v1/jobs');
  }

  async getJob(id: string) {
    return this.fetch(`/v1/jobs/${id}`);
  }
}

export const api = new ApiClient();
