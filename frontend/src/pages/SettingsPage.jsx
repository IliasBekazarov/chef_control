import { useState } from "react";
import { useTranslation } from "react-i18next";
import { useAuth } from "../context/AuthContext";
import { useTheme } from "../context/ThemeContext";
import { motion } from "framer-motion";
import { Sun, Moon, Globe, User, Save, Loader2 } from "lucide-react";
import api from "../api";

const LANGS = [
  { code: "ky", label: "Кыргызча" },
  { code: "ru", label: "Русский"  },
  { code: "en", label: "English"  },
];

export default function SettingsPage() {
  const { t, i18n } = useTranslation();
  const { dark, toggle } = useTheme();
  const { user }    = useAuth();

  const [form, setForm]   = useState({
    first_name: user?.first_name || "",
    last_name:  user?.last_name  || "",
    email:      user?.email      || "",
    location:   user?.profile?.location || "",
  });
  const [saving, setSaving]   = useState(false);
  const [success, setSuccess] = useState(false);

  const save = async () => {
    setSaving(true); setSuccess(false);
    try {
      await api.patch("/auth/me/", {
        first_name: form.first_name,
        last_name:  form.last_name,
        email:      form.email,
        profile:    { location: form.location },
      });
      setSuccess(true);
      setTimeout(() => setSuccess(false), 3000);
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="p-4 lg:p-6 max-w-2xl space-y-6 animate-fade-in">
      <div>
        <h1 className="text-2xl font-bold">{t("settings")}</h1>
        <p className="text-sm text-[var(--muted)]">Аккаунт жана колдонмо жөндөөлөрү</p>
      </div>

      {/* Profile */}
      <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }}
                  className="card p-6 space-y-5">
        <div className="flex items-center gap-3 border-b border-[var(--border)] pb-4">
          <User size={18} className="text-primary-500" />
          <h2 className="font-semibold">{t("profile")}</h2>
        </div>

        {/* Avatar */}
        <div className="flex items-center gap-4">
          <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-primary-400 to-primary-600
                          flex items-center justify-center text-white text-2xl font-bold">
            {(form.first_name || user?.username || "U")[0].toUpperCase()}
          </div>
          <div>
            <p className="font-semibold">{user?.full_name || user?.username}</p>
            <p className="text-sm text-[var(--muted)] capitalize">{user?.profile?.role || "user"}</p>
          </div>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium mb-1.5">{t("firstName")}</label>
            <input className="input" value={form.first_name}
                   onChange={(e) => setForm({ ...form, first_name: e.target.value })} />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1.5">{t("lastName")}</label>
            <input className="input" value={form.last_name}
                   onChange={(e) => setForm({ ...form, last_name: e.target.value })} />
          </div>
        </div>
        <div>
          <label className="block text-sm font-medium mb-1.5">{t("email")}</label>
          <input className="input" type="email" value={form.email}
                 onChange={(e) => setForm({ ...form, email: e.target.value })} />
        </div>
        <div>
          <label className="block text-sm font-medium mb-1.5">{t("location")}</label>
          <input className="input" placeholder="Кухня №1" value={form.location}
                 onChange={(e) => setForm({ ...form, location: e.target.value })} />
        </div>

        {success && (
          <motion.p initial={{ opacity: 0 }} animate={{ opacity: 1 }}
                    className="text-sm text-emerald-500 bg-emerald-50 dark:bg-emerald-900/20
                               border border-emerald-200 dark:border-emerald-800 rounded-xl px-4 py-2.5">
            ✓ Жөндөөлөр сакталды
          </motion.p>
        )}

        <button onClick={save} disabled={saving}
                className="btn-primary flex items-center gap-2">
          {saving ? <Loader2 size={16} className="animate-spin" /> : <Save size={16} />}
          {t("save")}
        </button>
      </motion.div>

      {/* Appearance */}
      <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.1 }} className="card p-6 space-y-5">
        <div className="flex items-center gap-3 border-b border-[var(--border)] pb-4">
          {dark ? <Moon size={18} className="text-primary-500" /> : <Sun size={18} className="text-primary-500" />}
          <h2 className="font-semibold">Внешний вид</h2>
        </div>

        {/* Theme */}
        <div className="flex items-center justify-between">
          <div>
            <p className="font-medium text-sm">Тема</p>
            <p className="text-xs text-[var(--muted)]">{dark ? "Карангы режим" : "Жарык режим"}</p>
          </div>
          <button onClick={toggle}
                  className={`relative w-12 h-6 rounded-full transition-colors duration-300
                             ${dark ? "bg-primary-500" : "bg-slate-300"}`}>
            <span className={`absolute top-0.5 left-0.5 w-5 h-5 rounded-full bg-white shadow transition-transform
                              ${dark ? "translate-x-6" : "translate-x-0"}`} />
          </button>
        </div>

        {/* Language */}
        <div>
          <div className="flex items-center gap-2 mb-3">
            <Globe size={16} className="text-[var(--muted)]" />
            <p className="font-medium text-sm">Тил / Язык / Language</p>
          </div>
          <div className="grid grid-cols-3 gap-2">
            {LANGS.map((l) => (
              <button key={l.code}
                onClick={() => { i18n.changeLanguage(l.code); localStorage.setItem("lang", l.code); }}
                className={`py-2.5 rounded-xl text-sm font-medium border transition
                  ${i18n.language === l.code
                    ? "border-primary-500 bg-primary-50 dark:bg-primary-900/20 text-primary-600"
                    : "border-[var(--border)] text-[var(--muted)] hover:border-primary-500"}`}>
                {l.label}
              </button>
            ))}
          </div>
        </div>
      </motion.div>
    </div>
  );
}
