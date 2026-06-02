import { TeamOutlined, TableOutlined } from '@ant-design/icons';
import { Layout, Menu, Typography } from 'antd';
import { useState } from 'react';
import { EmployeesPage } from './pages/EmployeesPage';
import { TimesheetPage } from './pages/TimesheetPage';

const { Header, Content, Sider } = Layout;

export function App() {
  const [page, setPage] = useState('timesheet');

  return (
    <Layout className="app-shell">
      <Sider breakpoint="lg" collapsedWidth="0" width={230} className="app-sider">
        <div className="brand">Uchet</div>
        <Menu
          theme="dark"
          mode="inline"
          selectedKeys={[page]}
          onClick={(item) => setPage(item.key)}
          items={[
            { key: 'timesheet', icon: <TableOutlined />, label: 'Табель' },
            { key: 'employees', icon: <TeamOutlined />, label: 'Сотрудники' },
          ]}
        />
      </Sider>
      <Layout>
        <Header className="app-header">
          <Typography.Title level={3}>{page === 'timesheet' ? 'Табель учета рабочего времени' : 'Сотрудники'}</Typography.Title>
        </Header>
        <Content className="app-content">{page === 'timesheet' ? <TimesheetPage /> : <EmployeesPage />}</Content>
      </Layout>
    </Layout>
  );
}
