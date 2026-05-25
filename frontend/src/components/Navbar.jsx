import { useTranslation } from "react-i18next";
import { Sun, Moon, Globe, LogOut, Menu, ChefHat } from "lucide-react";
import { useTheme } from "../context/ThemeContext";
import { useAuth } from "../context/AuthContext";
import { motion } from "framer-motion";
import { useState } from "react";

const LANGS = [
  { code: "ky", label: "Кырг" },
  { code: "ru", label: "Рус"  },
  { code: "en", label: "Eng"  },
];

export default function Navbar({ onMenuClick }) {
  const { dark, toggle }  = useTheme();
  const { user, logout }  = useAuth();
  const { i18n, t }       = useTranslation();
  const [langOpen, setLangOpen] = useState(false);

  const changeLang = (code) => {
    i18n.changeLanguage(code);
    localStorage.setItem("lang", code);
    setLangOpen(false);
  };

  return (
    <header className="sticky top-0 z-30 h-16 flex items-center gap-4 px-4 lg:px-6
                        bg-[var(--surface)] border-b border-[var(--border)] shadow-sm">
      {/* Hamburger */}
      <button onClick={onMenuClick}
              className="lg:hidden p-2 rounded-xl hover:bg-slate-100 dark:hover:bg-slate-800 transition">
        <Menu size={20} />
      </button>

      {/* Logo */}
      <div className="flex items-center gap-2 mr-auto">
        <div className="w-9 h-9 rounded-xl bg-primary-500 flex items-center justify-center">
          <ChefHat size={20} className="text-white" />
        </div>
        <span className="font-bold text-lg hidden sm:block">{t("appName")}</span>
      </div>

      {/* Controls */}
      <div className="flex items-center gap-2">
        {/* Language picker */}
        <div className="relative">
          <button onClick={() => setLangOpen((v) => !v)}
                  className="flex items-center gap-1.5 px-3 py-2 rounded-xl
                             text-sm font-medium text-[var(--muted)]
                             hover:bg-slate-100 dark:hover:bg-slate-800 transition">
            <Globe size={16} />
            <span className="hidden sm:inline uppercase text-xs tracking-wide">
              {i18n.language}
            </span>
          </button>
          {langOpen && (
            <motion.div initial={{ opacity: 0, y: -6 }} animate={{ opacity: 1, y: 0 }}
                        className="absolute right-0 top-12 w-28 card py-1 shadow-lg z-50">
              {LANGS.map((l) => (
                <button key={l.code} onClick={() => changeLang(l.code)}
                        className={`w-full text-left px-4 py-2 text-sm hover:bg-slate-100
                                   dark:hover:bg-slate-700 transition
                                   ${i18n.language === l.code ? "text-primary-500 font-semibold" : ""}`}>
                  {l.label}
                </button>
              ))}
            </motion.div>
          )}
        </div>

        {/* Theme toggle */}
        <button onClick={toggle}
                className="p-2 rounded-xl hover:bg-slate-100 dark:hover:bg-slate-800 transition text-[var(--muted)]">
          {dark ? <Sun size={18} /> : <Moon size={18} />}
        </button>

        {/* User avatar */}
        {user && (
          <div className="flex items-center gap-2 pl-2 border-l border-[var(--border)]">
            <div className="w-8 h-8 rounded-full bg-primary-500 flex items-center justify-center
                            text-white text-sm font-bold">
              {(user.first_name || user.username)[0].toUpperCase()}
            </div>
            <div className="hidden md:block text-right">
              <p className="text-sm font-semibold leading-none">{user.first_name || user.username}</p>
              <p className="text-xs text-[var(--muted)] capitalize">{user.profile?.role || "user"}</p>
            </div>
            <button onClick={logout}
                    className="p-2 rounded-xl text-[var(--muted)] hover:text-red-500
                               hover:bg-red-50 dark:hover:bg-red-900/20 transition ml-1">
              <LogOut size={16} />
            </button>
          </div>
        )}
      </div>
    </header>
  );
}
