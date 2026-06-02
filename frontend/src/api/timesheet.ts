import { api } from './client';
import type { TimesheetSummaryRow } from './types';

export async function fetchTimesheetSummary(year: number, month: number) {
  const response = await api.get<TimesheetSummaryRow[]>('/timesheet/summary', { params: { year, month } });
  return response.data;
}

export async function upsertTimesheetCell(employeeId: number, workDate: string, hoursWorked: number) {
  const response = await api.post('/timesheet/upsert', {
    employee_id: employeeId,
    work_date: workDate,
    hours_worked: hoursWorked,
    comment: 'Web',
  });
  return response.data;
}
