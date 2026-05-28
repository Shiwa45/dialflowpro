import axios from 'axios';

const api = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add tenant + auth headers
api.interceptors.request.use((config) => {
  const isAuthRequest =
    config.url?.includes('/accounts/users/login/') ||
    config.url?.includes('/accounts/users/register/') ||
    config.url?.includes('/auth/token/');

  const tenant = localStorage.getItem('tenant_schema');
  if (tenant && tenant !== 'null' && tenant !== 'undefined' && !isAuthRequest) {
    config.headers['X-Tenant'] = tenant;
  }

  const token = localStorage.getItem('access_token');
  if (token && token !== 'null' && token !== 'undefined' && !isAuthRequest) {
    config.headers.Authorization = `Bearer ${token}`;
  }

  return config;
});

// On 401, attempt a silent token refresh then retry once
let isRefreshing = false;
let refreshQueue: Array<(token: string) => void> = [];

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const original = error.config;

    // Only attempt refresh for 401s that haven't already been retried
    // and are not themselves auth/token requests
    if (
      error.response?.status !== 401 ||
      original._retry ||
      original.url?.includes('/auth/token/')
    ) {
      return Promise.reject(error);
    }

    const refreshToken = localStorage.getItem('refresh_token');
    if (!refreshToken || refreshToken === 'null' || refreshToken === 'undefined') {
      // No refresh token — force logout
      localStorage.clear();
      window.location.href = '/';
      return Promise.reject(error);
    }

    original._retry = true;

    if (isRefreshing) {
      // Queue this request until the in-flight refresh resolves
      return new Promise((resolve) => {
        refreshQueue.push((newToken: string) => {
          original.headers.Authorization = `Bearer ${newToken}`;
          resolve(api(original));
        });
      });
    }

    isRefreshing = true;
    try {
      const { data } = await axios.post('/api/auth/token/refresh/', {
        refresh: refreshToken,
      });

      const newAccess: string = data.access;
      localStorage.setItem('access_token', newAccess);
      // ROTATE_REFRESH_TOKENS=True means the server may return a new refresh token
      if (data.refresh) {
        localStorage.setItem('refresh_token', data.refresh);
      }

      // Flush queued requests
      refreshQueue.forEach((cb) => cb(newAccess));
      refreshQueue = [];

      original.headers.Authorization = `Bearer ${newAccess}`;
      return api(original);
    } catch {
      // Refresh failed — session is dead, clear storage and redirect to login
      refreshQueue = [];
      localStorage.clear();
      window.location.href = '/';
      return Promise.reject(error);
    } finally {
      isRefreshing = false;
    }
  }
);

export default api;
