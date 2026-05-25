import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { AuthProvider } from "./context/AuthContext";
import { ThemeProvider } from "./context/ThemeContext";
import "./i18n";

import Layout       from "./components/Layout";
import LoginPage    from "./pages/LoginPage";
import RegisterPage from "./pages/RegisterPage";
import DashboardPage from "./pages/DashboardPage";
import RecordsPage  from "./pages/RecordsPage";
import SessionsPage from "./pages/SessionsPage";
import UsersPage    from "./pages/UsersPage";
import SettingsPage from "./pages/SettingsPage";
import MonitorPage  from "./pages/MonitorPage";

export default function App() {
  return (
    <ThemeProvider>
      <AuthProvider>
        <BrowserRouter>
          <Routes>
            <Route path="/login"    element={<LoginPage />} />
            <Route path="/register" element={<RegisterPage />} />
            <Route path="/" element={<Layout />}>
              <Route index           element={<DashboardPage />} />
              <Route path="records"  element={<RecordsPage />} />
              <Route path="sessions" element={<SessionsPage />} />
              <Route path="monitor"  element={<MonitorPage />} />
              <Route path="users"    element={<UsersPage />} />
              <Route path="settings" element={<SettingsPage />} />
            </Route>
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </BrowserRouter>
      </AuthProvider>
    </ThemeProvider>
  );
}
