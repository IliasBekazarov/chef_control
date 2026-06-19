import { NavLink } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { useAuth } from "../context/AuthContext";
import { motion, AnimatePresence } from "framer-motion";
import {
  LayoutDashboard, ClipboardList, FolderOpen,
  Users, Settings, ChefHat, X, Activity, Brain,
} from "lucide-react";

export default function Sidebar({ open, onClose }) {
  const { t }    = useTranslation();
  const { isAdmin } = useAuth();

  const links = [
    { to: "/",         icon: LayoutDashboard, label: t("dashboard") },
    { to: "/monitor",  icon: Activity,        label: t("monitor"),  pulse: true },
    { to: "/records",  icon: ClipboardList,   label: t("records")   },
    { to: "/sessions", icon: FolderOpen,      label: t("sessions")  },
    ...(isAdmin()
      ? [
          { to: "/users",    icon: Users,  label: t("users") },
          { to: "/training", icon: Brain,  label: "ML Тренинг" },
        ]
      : []),
    { to: "/settings", icon: Settings, label: t("settings") },
  ];

  const SidebarContent = () => (
    <div className="flex flex-col h-full">
      {/* Logo */}
      <div className="h-16 flex items-center gap-3 px-5 border-b border-[var(--border)]">
        <div className="w-9 h-9 rounded-xl bg-primary-500 flex items-center justify-center flex-shrink-0">
          <ChefHat size={20} className="text-white" />
        </div>
        <div>
          <p className="font-bold text-sm leading-none">Chef Control</p>
          <p className="text-xs text-[var(--muted)] mt-0.5">Kitchen Monitor</p>
        </div>
        {/* Mobile close */}
        <button onClick={onClose} className="ml-auto lg:hidden p-1 rounded-lg
                                              hover:bg-slate-100 dark:hover:bg-slate-800 transition">
          <X size={18} />
        </button>
      </div>

      {/* Nav */}
      <nav className="flex-1 overflow-y-auto py-4 px-3 space-y-1">
        {links.map(({ to, icon: Icon, label, pulse }) => (
          <NavLink key={to} to={to} end={to === "/"}
            onClick={onClose}
            className={({ isActive }) =>
              `flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all duration-150
               ${isActive
                 ? "bg-primary-500 text-white shadow-md shadow-primary-500/25"
                 : "text-[var(--muted)] hover:text-[var(--text)] hover:bg-slate-100 dark:hover:bg-slate-800"}`
            }>
            <div className="relative">
              <Icon size={18} />
              {pulse && (
                <span className="absolute -top-0.5 -right-0.5 w-2 h-2 bg-emerald-400 rounded-full animate-pulse" />
              )}
            </div>
            {label}
          </NavLink>
        ))}
      </nav>

      {/* Footer */}
      <div className="p-4 border-t border-[var(--border)]">
        <p className="text-xs text-[var(--muted)] text-center">Chef Control v1.0</p>
      </div>
    </div>
  );

  return (
    <>
      {/* Desktop sidebar */}
      <aside className="hidden lg:flex flex-col w-60 flex-shrink-0 h-screen sticky top-0
                        bg-[var(--surface)] border-r border-[var(--border)]">
        <SidebarContent />
      </aside>

      {/* Mobile overlay */}
      <AnimatePresence>
        {open && (
          <>
            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
                        onClick={onClose}
                        className="fixed inset-0 z-40 bg-black/50 lg:hidden" />
            <motion.aside
              initial={{ x: -280 }} animate={{ x: 0 }} exit={{ x: -280 }}
              transition={{ type: "spring", damping: 25, stiffness: 300 }}
              className="fixed left-0 top-0 bottom-0 z-50 w-64 flex flex-col
                         bg-[var(--surface)] border-r border-[var(--border)] shadow-xl lg:hidden">
              <SidebarContent />
            </motion.aside>
          </>
        )}
      </AnimatePresence>
    </>
  );
}
