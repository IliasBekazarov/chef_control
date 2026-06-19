import axios from "axios";

// Dev: VITE_API_URL жок → Vite proxy аркылуу /api (localhost:8000)
// Prod: VITE_API_URL=https://your-backend.railway.app
const BASE_URL = import.meta.env.VITE_API_URL ?? "";

const api = axios.create({ baseURL: `${BASE_URL}/api` });

api.interceptors.request.use((cfg) => {
  const token = localStorage.getItem("access");
  if (token) cfg.headers.Authorization = `Bearer ${token}`;
  return cfg;
});

api.interceptors.response.use(
  (r) => r,
  async (err) => {
    const orig = err.config;
    if (err.response?.status === 401 && !orig._retry) {
      orig._retry = true;
      const refresh = localStorage.getItem("refresh");
      if (refresh) {
        try {
          const { data } = await axios.post(`${BASE_URL}/api/auth/refresh/`, { refresh });
          localStorage.setItem("access", data.access);
          orig.headers.Authorization = `Bearer ${data.access}`;
          return api(orig);
        } catch {
          localStorage.clear();
          window.location.href = "/login";
        }
      }
    }
    return Promise.reject(err);
  }
);

export default api;
