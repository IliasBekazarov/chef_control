import { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { useTranslation } from "react-i18next";
import { motion } from "framer-motion";
import { ChefHat, Eye, EyeOff, Loader2 } from "lucide-react";

export default function LoginPage() {
  const { login }     = useAuth();
  const navigate      = useNavigate();
  const { t, i18n }  = useTranslation();
  const [form, setForm]       = useState({ username: "", password: "" });
  const [showPass, setShowPass] = useState(false);
  const [loading, setLoading]   = useState(false);
  const [error, setError]       = useState("");

  const LANGS = [
    { code: "ky", label: "Кырг" },
    { code: "ru", label: "Рус"  },
    { code: "en", label: "Eng"  },
  ];

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError("");
    try {
      await login(form.username, form.password);
      navigate("/");
    } catch {
      setError("Колдонуучу аты же сырсөз туура эмес");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[var(--bg)] flex items-center justify-center p-4">
      {/* Background decoration */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute -top-40 -right-40 w-96 h-96 bg-primary-500/10 rounded-full blur-3xl" />
        <div className="absolute -bottom-40 -left-40 w-96 h-96 bg-blue-500/10 rounded-full blur-3xl" />
      </div>

      <motion.div
        initial={{ opacity: 0, y: 24 }}
        animate={{ opacity: 1, y: 0 }}
        className="relative w-full max-w-md">

        {/* Lang switcher */}
        <div className="flex justify-center gap-2 mb-6">
          {LANGS.map((l) => (
            <button key={l.code}
              onClick={() => { i18n.changeLanguage(l.code); localStorage.setItem("lang", l.code); }}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition
                ${i18n.language === l.code
                  ? "bg-primary-500 text-white"
                  : "bg-[var(--surface)] text-[var(--muted)] border border-[var(--border)] hover:border-primary-500"}`}>
              {l.label}
            </button>
          ))}
        </div>

        <div className="card p-8 shadow-xl">
          {/* Logo */}
          <div className="text-center mb-8">
            <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-primary-400 to-primary-600
                            flex items-center justify-center mx-auto mb-4 shadow-lg shadow-primary-500/30">
              <ChefHat size={32} className="text-white" />
            </div>
            <h1 className="text-2xl font-bold">{t("appName")}</h1>
            <p className="text-sm text-[var(--muted)] mt-1">{t("appDesc")}</p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium mb-1.5">{t("username")}</label>
              <input className="input" placeholder={t("username")}
                     value={form.username}
                     onChange={(e) => setForm({ ...form, username: e.target.value })}
                     required autoFocus />
            </div>

            <div>
              <label className="block text-sm font-medium mb-1.5">{t("password")}</label>
              <div className="relative">
                <input className="input pr-10"
                       type={showPass ? "text" : "password"}
                       placeholder={t("password")}
                       value={form.password}
                       onChange={(e) => setForm({ ...form, password: e.target.value })}
                       required />
                <button type="button" onClick={() => setShowPass((v) => !v)}
                        className="absolute right-3 top-1/2 -translate-y-1/2 text-[var(--muted)]">
                  {showPass ? <EyeOff size={16} /> : <Eye size={16} />}
                </button>
              </div>
            </div>

            {error && (
              <motion.p initial={{ opacity: 0 }} animate={{ opacity: 1 }}
                        className="text-sm text-red-500 bg-red-50 dark:bg-red-900/20
                                   border border-red-200 dark:border-red-800 rounded-xl px-4 py-2.5">
                {error}
              </motion.p>
            )}

            <button type="submit" disabled={loading} className="btn-primary w-full flex items-center justify-center gap-2 mt-2">
              {loading && <Loader2 size={16} className="animate-spin" />}
              {t("login")}
            </button>
          </form>

          <p className="text-center text-sm text-[var(--muted)] mt-6">
            Каттоо жок болсо{" "}
            <Link to="/register" className="text-primary-500 font-semibold hover:underline">
              {t("register")}
            </Link>
          </p>
        </div>
      </motion.div>
    </div>
  );
}
