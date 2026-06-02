import { api } from './client';
import type { Employee, EmployeePayload } from './types';

export async function fetchEmployees(search?: string) {
  const response = await api.get<Employee[]>('/employees', { params: { search: search || undefined } });
  return response.data;
}

export async function createEmployee(payload: EmployeePayload) {
  const response = await api.post<Employee>('/employees', payload);
  return response.data;
}

export async function updateEmployee(id: number, payload: Partial<EmployeePayload>) {
  const response = await api.put<Employee>(`/employees/${id}`, payload);
  return response.data;
}

export async function deleteEmployee(id: number) {
  await api.delete(`/employees/${id}`);
}
