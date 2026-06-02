import { DeleteOutlined, EditOutlined, PlusOutlined, SearchOutlined } from '@ant-design/icons';
import { Button, Form, Input, InputNumber, Modal, Popconfirm, Select, Space, Table, message } from 'antd';
import { useEffect, useState } from 'react';
import { createEmployee, deleteEmployee, fetchEmployees, updateEmployee } from '../api/employees';
import { paymentTypeLabels, type Employee, type EmployeePayload, type PaymentType } from '../api/types';

const paymentOptions = [
  { value: 'hourly', label: paymentTypeLabels.hourly },
  { value: 'shift', label: paymentTypeLabels.shift },
  { value: 'fixed', label: paymentTypeLabels.fixed },
];

export function EmployeesPage() {
  const [employees, setEmployees] = useState<Employee[]>([]);
  const [loading, setLoading] = useState(false);
  const [search, setSearch] = useState('');
  const [editing, setEditing] = useState<Employee | null>(null);
  const [open, setOpen] = useState(false);
  const [form] = Form.useForm<EmployeePayload>();

  const load = async () => {
    setLoading(true);
    try {
      setEmployees(await fetchEmployees(search));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void load();
  }, []);

  const submit = async () => {
    const values = await form.validateFields();
    if (editing) {
      await updateEmployee(editing.id, values);
      message.success('Сотрудник обновлен');
    } else {
      await createEmployee(values);
      message.success('Сотрудник создан');
    }
    setOpen(false);
    setEditing(null);
    form.resetFields();
    await load();
  };

  return (
    <div className="page-panel">
      <div className="toolbar">
        <Input
          prefix={<SearchOutlined />}
          placeholder="Поиск по ФИО"
          value={search}
          onChange={(event) => setSearch(event.target.value)}
          onPressEnter={load}
          allowClear
        />
        <Button onClick={load}>Найти</Button>
        <Button
          type="primary"
          icon={<PlusOutlined />}
          onClick={() => {
            setEditing(null);
            form.resetFields();
            form.setFieldsValue({ payment_type: 'hourly', hourly_rate: 0 });
            setOpen(true);
          }}
        >
          Добавить
        </Button>
      </div>
      <Table
        rowKey="id"
        loading={loading}
        dataSource={employees}
        pagination={{ pageSize: 10 }}
        columns={[
          { title: 'ID', dataIndex: 'id', width: 80 },
          { title: 'ФИО', dataIndex: 'full_name' },
          {
            title: 'Тип оплаты',
            dataIndex: 'payment_type',
            width: 150,
            render: (type: PaymentType) => paymentTypeLabels[type] ?? type,
          },
          {
            title: 'Ставка, ₸/час',
            dataIndex: 'hourly_rate',
            width: 150,
            render: (value: string) => `${Number(value).toLocaleString('ru-RU')} ₸`,
          },
          { title: 'Примечания', dataIndex: 'notes' },
          {
            title: '',
            width: 120,
            render: (_, record) => (
              <Space>
                <Button
                  icon={<EditOutlined />}
                  onClick={() => {
                    setEditing(record);
                    form.setFieldsValue({
                      full_name: record.full_name,
                      payment_type: record.payment_type as PaymentType,
                      hourly_rate: Number(record.hourly_rate),
                      notes: record.notes,
                    });
                    setOpen(true);
                  }}
                />
                <Popconfirm title="Удалить сотрудника?" onConfirm={async () => { await deleteEmployee(record.id); await load(); }}>
                  <Button danger icon={<DeleteOutlined />} />
                </Popconfirm>
              </Space>
            ),
          },
        ]}
      />
      <Modal title={editing ? 'Редактировать сотрудника' : 'Новый сотрудник'} open={open} onOk={submit} onCancel={() => setOpen(false)} okText="Сохранить" cancelText="Отмена">
        <Form form={form} layout="vertical">
          <Form.Item name="full_name" label="ФИО" rules={[{ required: true, message: 'Введите ФИО' }]}>
            <Input />
          </Form.Item>
          <Form.Item name="payment_type" label="Тип оплаты" rules={[{ required: true }]}>
            <Select options={paymentOptions} />
          </Form.Item>
          <Form.Item name="hourly_rate" label="Ставка, ₸/час" rules={[{ required: true }]}>
            <InputNumber min={0} precision={2} className="wide-control" />
          </Form.Item>
          <Form.Item name="notes" label="Примечания">
            <Input.TextArea rows={3} />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
}
