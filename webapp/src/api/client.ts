import axios from "axios";

const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || window.location.origin,
  timeout: 15000,
  headers: {
    "Content-Type": "application/json",
  },
});

apiClient.interceptors.request.use((config) => {
  try {
    const webApp = window.Telegram?.WebApp;
    if (webApp?.initData) {
      config.headers.Authorization = `tma ${webApp.initData}`;
    }
  } catch {
    // Not in Telegram context
  }
  return config;
});

apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (axios.isAxiosError(error)) {
      const message =
        error.response?.data?.detail ||
        error.response?.data?.message ||
        error.message ||
        "An unexpected error occurred";

      console.error(`[API Error] ${error.config?.url}: ${message}`);
    }
    return Promise.reject(error);
  }
);

export default apiClient;
