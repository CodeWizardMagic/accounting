import axios from 'axios';

const defaultApiUrl = `${window.location.protocol}//${window.location.hostname}:8010`;

export const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || defaultApiUrl,
});
