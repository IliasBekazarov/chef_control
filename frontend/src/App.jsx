import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { AuthProvider, useAuth } from "./context/AuthContext";
import { ThemeProvider } from "./context/ThemeContext";
import "./i18n";

import Layout        from "./components/Layout";
import LoginPage     from "./pages/LoginPage";
import DashboardPage from "./pages/DashboardPage";
import RecordsPage   from "./pages/RecordsPage";
import SessionsPage  from "./pages/SessionsPage";
import UsersPage     from "./pages/UsersPage";
import SettingsPage  from "./pages/SettingsPage";
import MonitorPage   from "./pages/MonitorPage";
import TrainingPage  from "./pages/TrainingPage";

// Логин болбосо /login'га жөнөтөт
function AdminRoute({ children }) {
  const { user, loading } = useAuth();
  if (loading) return null;
  return user ? children : <Navigate to="/login" replace />;
}

export default function App() {
  return (
    <ThemeProvider>
      <AuthProvider>
        <BrowserRouter>
          <Routes>
            <Route path="/login" element={<LoginPage />} />
            <Route path="/" element={<Layout />}>
              {/* Ачык баракчалар — логинсиз кирсе болот */}
              <Route index           element={<DashboardPage />} />
              <Route path="monitor"  element={<MonitorPage />} />
              <Route path="records"  element={<RecordsPage />} />
              <Route path="sessions" element={<SessionsPage />} />
              {/* Admin гана баракчалар */}
              <Route path="users"    element={<AdminRoute><UsersPage /></AdminRoute>} />
              <Route path="training" element={<AdminRoute><TrainingPage /></AdminRoute>} />
              <Route path="settings" element={<AdminRoute><SettingsPage /></AdminRoute>} />
            </Route>
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </BrowserRouter>
      </AuthProvider>
    </ThemeProvider>
  );
}
