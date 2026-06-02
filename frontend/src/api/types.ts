export type PaymentType = 'hourly' | 'shift' | 'fixed';

export const paymentTypeLabels: Record<PaymentType, string> = {
  hourly: 'Почасово',
  shift: 'Посменно',
  fixed: 'Фиксированно',
};

export interface Employee {
  id: number;
  full_name: string;
  payment_type: PaymentType;
  hourly_rate: string;
  notes?: string | null;
  created_at: string;
  updated_at: string;
}

export interface EmployeePayload {
  full_name: string;
  payment_type: PaymentType;
  hourly_rate: number;
  notes?: string | null;
}

export interface TimesheetSummaryRow {
  employee_id: number;
  employee_name: string;
  payment_type: PaymentType;
  hourly_rate: string;
  days: Record<string, string>;
  working_days: number;
  total_hours: string;
  estimated_salary: string;
}
