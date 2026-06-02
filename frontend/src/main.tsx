import React from 'react';
import ReactDOM from 'react-dom/client';
import { ConfigProvider } from 'antd';
import ruRU from 'antd/locale/ru_RU';
import dayjs from 'dayjs';
import 'antd/dist/reset.css';
import 'dayjs/locale/ru';
import './styles.css';
import { App } from './App';

dayjs.locale('ru');

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <ConfigProvider locale={ruRU}>
      <App />
    </ConfigProvider>
  </React.StrictMode>,
);
