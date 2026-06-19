import { useState, useEffect } from "react";
import { useTranslation } from "react-i18next";
import { useAuth } from "../context/AuthContext";
import { useTheme } from "../context/ThemeContext";
import { motion, AnimatePresence } from "framer-motion";
import {
  Sun, Moon, Globe, User, Save, Loader2,
  Bell, BellOff, Send, CheckCircle2, XCircle, ChevronDown,
  Camera, CameraOff,
} from "lucide-react";
import api from "../api";

const LANGS = [
  { code: "ky", label: "Кыргызча" },
  { code: "ru", label: "Русский"  },
  { code: "en", label: "English"  },
];

const FADE_UP = (delay = 0) => ({
  initial:   { opacity: 0, y: 16 },
  animate:   { opacity: 1, y: 0 },
  transition: { delay },
});

// ─── Profile section ────────────────────────────────────────────────────────
function ProfileSection({ user }) {
  const { t } = useTranslation();
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
    <motion.div {...FADE_UP(0)} className="card p-6 space-y-5">
      <div className="flex items-center gap-3 border-b border-[var(--border)] pb-4">
        <User size={18} className="text-primary-500" />
        <h2 className="font-semibold">{t("profile")}</h2>
      </div>

      <div className="flex items-center gap-4">
        <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-primary-400 to-primary-600
                        flex items-center justify-center text-white text-2xl font-bold select-none">
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

      <AnimatePresence>
        {success && (
          <motion.p key="ok" initial={{ opacity: 0, y: -4 }} animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0 }}
                    className="text-sm text-emerald-600 bg-emerald-50 dark:bg-emerald-900/20
                               border border-emerald-200 dark:border-emerald-800 rounded-xl px-4 py-2.5 flex items-center gap-2">
            <CheckCircle2 size={15} /> Жөндөөлөр сакталды
          </motion.p>
        )}
      </AnimatePresence>

      <button onClick={save} disabled={saving}
              className="btn-primary flex items-center gap-2">
        {saving ? <Loader2 size={16} className="animate-spin" /> : <Save size={16} />}
        {t("save")}
      </button>
    </motion.div>
  );
}

// ─── Telegram alert section ──────────────────────────────────────────────────
function TelegramSection() {
  const [cfg, setCfg]         = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving]   = useState(false);
  const [testing, setTesting] = useState(false);
  const [feedback, setFeedback] = useState(null); // { ok, msg }

  useEffect(() => {
    api.get("/settings/alerts/")
      .then((r) => setCfg(r.data))
      .catch(() => setCfg({ enabled: false, bot_token: "", chat_id: "",
                            violation_threshold: 1, cooldown_minutes: 5,
                            last_alert_at: null, consecutive_violations: 0 }))
      .finally(() => setLoading(false));
  }, []);

  const set = (key, val) => setCfg((prev) => ({ ...prev, [key]: val }));

  const save = async () => {
    setSaving(true); setFeedback(null);
    try {
      const r = await api.put("/settings/alerts/", {
        enabled:             cfg.enabled,
        bot_token:           cfg.bot_token,
        chat_id:             cfg.chat_id,
        violation_threshold: cfg.violation_threshold,
        cooldown_minutes:    cfg.cooldown_minutes,
      });
      setCfg(r.data);
      setFeedback({ ok: true, msg: "Жөндөөлөр сакталды ✅" });
    } catch {
      setFeedback({ ok: false, msg: "Сактоодо ката чыкты" });
    } finally {
      setSaving(false);
      setTimeout(() => setFeedback(null), 4000);
    }
  };

  const test = async () => {
    if (!cfg.bot_token || !cfg.chat_id) {
      setFeedback({ ok: false, msg: "Алгач Bot Token жана Chat ID толтуруңуз" });
      setTimeout(() => setFeedback(null), 4000);
      return;
    }
    setTesting(true); setFeedback(null);
    try {
      await api.post("/settings/alerts/test/", {
        bot_token: cfg.bot_token,
        chat_id:   cfg.chat_id,
      });
      setFeedback({ ok: true, msg: "Тест алерт жиберилди — Telegram'ды текшериңиз 📲" });
    } catch (e) {
      const err = e?.response?.data?.error || "Telegram API ката кайтарды";
      setFeedback({ ok: false, msg: err });
    } finally {
      setTesting(false);
      setTimeout(() => setFeedback(null), 6000);
    }
  };

  if (loading) {
    return (
      <motion.div {...FADE_UP(0.2)} className="card p-6 flex items-center gap-3 text-[var(--muted)]">
        <Loader2 size={18} className="animate-spin" />
        <span className="text-sm">Telegram жөндөөлөрү жүктөлүп жатат…</span>
      </motion.div>
    );
  }

  return (
    <motion.div {...FADE_UP(0.2)} className="card p-6 space-y-5">
      {/* Header + toggle */}
      <div className="flex items-center justify-between border-b border-[var(--border)] pb-4">
        <div className="flex items-center gap-3">
          {cfg.enabled
            ? <Bell size={18} className="text-primary-500" />
            : <BellOff size={18} className="text-[var(--muted)]" />}
          <div>
            <h2 className="font-semibold">Telegram алерттер</h2>
            <p className="text-xs text-[var(--muted)]">Бузуу болгондо Telegram'га билдируу</p>
          </div>
        </div>
        <button
          onClick={() => set("enabled", !cfg.enabled)}
          className={`relative w-12 h-6 rounded-full transition-colors duration-300
                     ${cfg.enabled ? "bg-primary-500" : "bg-slate-300 dark:bg-slate-600"}`}
          aria-label="Toggle alerts"
        >
          <span className={`absolute top-0.5 left-0.5 w-5 h-5 rounded-full bg-white shadow
                            transition-transform duration-300
                            ${cfg.enabled ? "translate-x-6" : "translate-x-0"}`} />
        </button>
      </div>

      {/* How-to hint */}
      <details className="group">
        <summary className="flex items-center gap-2 text-sm text-[var(--muted)] cursor-pointer
                            select-none list-none hover:text-[var(--text)] transition">
          <ChevronDown size={14} className="transition-transform group-open:rotate-180" />
          Bot кантип жасалат?
        </summary>
        <div className="mt-3 text-xs text-[var(--muted)] space-y-1 pl-4 border-l-2 border-[var(--border)]">
          <p>1. Telegram'да <code className="bg-[var(--border)] px-1 rounded">@BotFather</code>'га жазыңыз</p>
          <p>2. <code className="bg-[var(--border)] px-1 rounded">/newbot</code> командасын жиберип, токен алыңыз</p>
          <p>3. Бот'уңузга жазыңыз же аны топко кошуңуз</p>
          <p>4. Chat ID үчүн <code className="bg-[var(--border)] px-1 rounded">@userinfobot</code>'ка жазыңыз</p>
        </div>
      </details>

      {/* Fields */}
      <div className="space-y-4">
        <div>
          <label className="block text-sm font-medium mb-1.5">Bot Token</label>
          <input
            className="input font-mono text-sm"
            placeholder="1234567890:ABCdef..."
            type="password"
            value={cfg.bot_token}
            onChange={(e) => set("bot_token", e.target.value)}
          />
        </div>
        <div>
          <label className="block text-sm font-medium mb-1.5">Chat ID</label>
          <input
            className="input font-mono text-sm"
            placeholder="-1001234567890 же 123456789"
            value={cfg.chat_id}
            onChange={(e) => set("chat_id", e.target.value)}
          />
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium mb-1.5">
              Threshold
              <span className="ml-1 text-[var(--muted)] font-normal">(катары бузуулар)</span>
            </label>
            <select
              className="input"
              value={cfg.violation_threshold}
              onChange={(e) => set("violation_threshold", Number(e.target.value))}
            >
              {[1, 2, 3, 5].map((n) => (
                <option key={n} value={n}>{n} ирет</option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium mb-1.5">
              Cooldown
              <span className="ml-1 text-[var(--muted)] font-normal">(мин)</span>
            </label>
            <select
              className="input"
              value={cfg.cooldown_minutes}
              onChange={(e) => set("cooldown_minutes", Number(e.target.value))}
            >
              {[1, 5, 10, 15, 30].map((n) => (
                <option key={n} value={n}>{n} мин</option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* Last alert info */}
      {cfg.last_alert_at && (
        <p className="text-xs text-[var(--muted)]">
          Акыркы алерт: {new Date(cfg.last_alert_at).toLocaleString("ru-RU")}
        </p>
      )}

      {/* Feedback */}
      <AnimatePresence>
        {feedback && (
          <motion.div
            key="fb"
            initial={{ opacity: 0, y: -4 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }}
            className={`flex items-center gap-2 text-sm rounded-xl px-4 py-2.5 border
              ${feedback.ok
                ? "text-emerald-600 bg-emerald-50 dark:bg-emerald-900/20 border-emerald-200 dark:border-emerald-800"
                : "text-red-600 bg-red-50 dark:bg-red-900/20 border-red-200 dark:border-red-800"}`}
          >
            {feedback.ok ? <CheckCircle2 size={15} /> : <XCircle size={15} />}
            {feedback.msg}
          </motion.div>
        )}
      </AnimatePresence>

      {/* Actions */}
      <div className="flex items-center gap-3 pt-1">
        <button onClick={save} disabled={saving}
                className="btn-primary flex items-center gap-2 flex-1">
          {saving ? <Loader2 size={16} className="animate-spin" /> : <Save size={16} />}
          Сактоо
        </button>
        <button onClick={test} disabled={testing || saving}
                className="btn-secondary flex items-center gap-2 flex-1">
          {testing ? <Loader2 size={16} className="animate-spin" /> : <Send size={16} />}
          Тест жиберүү
        </button>
      </div>
    </motion.div>
  );
}

// ─── Camera Control section ──────────────────────────────────────────────────
function CameraSection() {
  const [running, setRunning] = useState(null);
  const [pending, setPending] = useState(false);
  const [error,   setError]   = useState(null);

  useEffect(() => {
    const fetch = () =>
      api.get("/camera/").then((r) => setRunning(r.data.running)).catch(() => {});
    fetch();
    const iv = setInterval(fetch, 5000);
    return () => clearInterval(iv);
  }, []);

  const toggle = async () => {
    setPending(true); setError(null);
    try {
      const { data } = await api.post("/camera/", { action: running ? "stop" : "start" });
      setRunning(data.running);
    } catch {
      setError("Ката чыкты — Django иштеп жатканын текшер");
    } finally {
      setPending(false);
    }
  };

  return (
    <motion.div {...FADE_UP(0.15)} className="card p-6 space-y-5">
      <div className="flex items-center justify-between border-b border-[var(--border)] pb-4">
        <div className="flex items-center gap-3">
          <Camera size={18} className={running ? "text-emerald-500" : "text-[var(--muted)]"} />
          <div>
            <h2 className="font-semibold">Камера</h2>
            <p className="text-xs text-[var(--muted)]">Аш үй детекциясын башкаруу</p>
          </div>
        </div>
        {running === null ? (
          <Loader2 size={15} className="animate-spin text-[var(--muted)]" />
        ) : (
          <span className={`text-xs font-semibold px-2.5 py-1 rounded-full ${
            running
              ? "bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400"
              : "bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-400"
          }`}>
            {running ? "● Иштеп жатат" : "○ Токтогон"}
          </span>
        )}
      </div>

      <AnimatePresence>
        {error && (
          <motion.p key="err" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
                    className="text-sm text-red-500 flex items-center gap-2">
            <XCircle size={14} /> {error}
          </motion.p>
        )}
      </AnimatePresence>

      <button
        onClick={toggle}
        disabled={pending || running === null}
        className={`w-full flex items-center justify-center gap-2 py-3 rounded-xl font-semibold transition
          ${running
            ? "bg-red-100 text-red-600 hover:bg-red-200 dark:bg-red-900/20 dark:text-red-400 dark:hover:bg-red-900/30"
            : "btn-primary"}`}
      >
        {pending ? (
          <Loader2 size={16} className="animate-spin" />
        ) : running ? (
          <><CameraOff size={16} /> Камераны өчүрүү</>
        ) : (
          <><Camera size={16} /> Камераны күйгүзүү</>
        )}
      </button>
    </motion.div>
  );
}

// ─── Appearance section ──────────────────────────────────────────────────────
function AppearanceSection({ dark, toggle }) {
  const { i18n } = useTranslation();
  return (
    <motion.div {...FADE_UP(0.1)} className="card p-6 space-y-5">
      <div className="flex items-center gap-3 border-b border-[var(--border)] pb-4">
        {dark ? <Moon size={18} className="text-primary-500" /> : <Sun size={18} className="text-primary-500" />}
        <h2 className="font-semibold">Внешний вид</h2>
      </div>

      <div className="flex items-center justify-between">
        <div>
          <p className="font-medium text-sm">Тема</p>
          <p className="text-xs text-[var(--muted)]">{dark ? "Карангы режим" : "Жарык режим"}</p>
        </div>
        <button onClick={toggle}
                className={`relative w-12 h-6 rounded-full transition-colors duration-300
                           ${dark ? "bg-primary-500" : "bg-slate-300"}`}>
          <span className={`absolute top-0.5 left-0.5 w-5 h-5 rounded-full bg-white shadow
                            transition-transform ${dark ? "translate-x-6" : "translate-x-0"}`} />
        </button>
      </div>

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
  );
}

// ─── Page ────────────────────────────────────────────────────────────────────
export default function SettingsPage() {
  const { t }       = useTranslation();
  const { dark, toggle } = useTheme();
  const { user }    = useAuth();
  const isAdmin     = user?.profile?.role === "admin" || user?.is_staff;

  return (
    <div className="p-4 lg:p-6 max-w-2xl space-y-6 animate-fade-in">
      <div>
        <h1 className="text-2xl font-bold">{t("settings")}</h1>
        <p className="text-sm text-[var(--muted)]">Аккаунт жана колдонмо жөндөөлөрү</p>
      </div>

      <ProfileSection user={user} />
      {isAdmin && <CameraSection />}
      {isAdmin && <TelegramSection />}
      <AppearanceSection dark={dark} toggle={toggle} />
    </div>
  );
}
