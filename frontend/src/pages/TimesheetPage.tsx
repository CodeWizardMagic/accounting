import { SaveOutlined, ReloadOutlined } from '@ant-design/icons';
import { Button, DatePicker, InputNumber, Space, Table, Tag, message } from 'antd';
import dayjs, { Dayjs } from 'dayjs';
import { useEffect, useMemo, useState } from 'react';
import { fetchTimesheetSummary, upsertTimesheetCell } from '../api/timesheet';
import { paymentTypeLabels, type TimesheetSummaryRow } from '../api/types';

type Drafts = Record<string, number>;

function key(employeeId: number, day: number) {
  return `${employeeId}:${day}`;
}

export function TimesheetPage() {
  const [month, setMonth] = useState<Dayjs>(dayjs());
  const [rows, setRows] = useState<TimesheetSummaryRow[]>([]);
  const [loading, setLoading] = useState(false);
  const [drafts, setDrafts] = useState<Drafts>({});

  const daysInMonth = month.daysInMonth();

  const load = async () => {
    setLoading(true);
    try {
      setRows(await fetchTimesheetSummary(month.year(), month.month() + 1));
      setDrafts({});
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void load();
  }, [month]);

  const save = async () => {
    const entries = Object.entries(drafts);
    for (const [draftKey, value] of entries) {
      const [employeeId, day] = draftKey.split(':').map(Number);
      const workDate = month.date(day).format('YYYY-MM-DD');
      await upsertTimesheetCell(employeeId, workDate, value);
    }
    message.success(`Сохранено ячеек: ${entries.length}`);
    await load();
  };

  const columns = useMemo(() => {
    const dayColumns = Array.from({ length: daysInMonth }, (_, index) => {
      const day = index + 1;
      return {
        title: String(day),
        dataIndex: ['days', String(day)],
        width: 74,
        align: 'center' as const,
        render: (value: string, record: TimesheetSummaryRow) => {
          const draftKey = key(record.employee_id, day);
          const current = drafts[draftKey] ?? Number(value || 0);
          const changed = draftKey in drafts;
          return (
            <InputNumber
              min={0}
              max={24}
              precision={2}
              size="small"
              value={current}
              className={changed ? 'cell-input changed' : 'cell-input'}
              onChange={(next) => {
                setDrafts((prev) => ({ ...prev, [draftKey]: Number(next || 0) }));
              }}
            />
          );
        },
      };
    });

    return [
      {
        title: 'Сотрудник',
        dataIndex: 'employee_name',
        fixed: 'left' as const,
        width: 220,
        render: (name: string, record: TimesheetSummaryRow) => (
          <Space direction="vertical" size={0}>
            <span className="employee-name">{name}</span>
            <Tag color={record.payment_type === 'hourly' ? 'green' : 'blue'}>
              {paymentTypeLabels[record.payment_type] ?? record.payment_type}
            </Tag>
          </Space>
        ),
      },
      ...dayColumns,
      { title: 'Дней', dataIndex: 'working_days', fixed: 'right' as const, width: 90 },
      { title: 'Часов', dataIndex: 'total_hours', fixed: 'right' as const, width: 100 },
      {
        title: 'Зарплата, ₸',
        dataIndex: 'estimated_salary',
        fixed: 'right' as const,
        width: 150,
        render: (value: string) => `${Number(value).toLocaleString('ru-RU')} ₸`,
      },
    ];
  }, [daysInMonth, drafts]);

  return (
    <div className="page-panel">
      <div className="toolbar">
        <DatePicker picker="month" value={month} onChange={(value) => value && setMonth(value)} allowClear={false} />
        <Button icon={<ReloadOutlined />} onClick={load}>Обновить</Button>
        <Button type="primary" icon={<SaveOutlined />} disabled={Object.keys(drafts).length === 0} onClick={save}>
          Сохранить изменения
        </Button>
        <span className="muted">Изменено ячеек: {Object.keys(drafts).length}</span>
      </div>
      <Table
        rowKey="employee_id"
        loading={loading}
        columns={columns}
        dataSource={rows}
        pagination={false}
        scroll={{ x: 220 + daysInMonth * 74 + 340, y: 'calc(100vh - 230px)' }}
        bordered
        size="small"
        className="excel-table"
      />
    </div>
  );
}
