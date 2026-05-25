import { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { motion } from "framer-motion";
import { ChefHat, Loader2 } from "lucide-react";
import api from "../api";

export default function RegisterPage() {
  const navigate    = useNavigate();
  const { t }       = useTranslation();
  const [form, setForm] = useState({
    username: "", email: "", first_name: "", last_name: "",
    password: "", password2: "", role: "user",
  });
  const [loading, setLoading] = useState(false);
  const [error, setError]     = useState("");

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (form.password !== form.password2) {
      setError("Сырсөздөр дал келбейт"); return;
    }
    setLoading(true); setError("");
    try {
      await api.post("/auth/register/", form);
      navigate("/login");
    } catch (err) {
      const d = err.response?.data;
      setError(d ? Object.values(d).flat().join(" ") : "Ката болду");
    } finally {
      setLoading(false);
    }
  };

  const field = (key, label, type = "text") => (
    <div>
      <label className="block text-sm font-medium mb-1.5">{label}</label>
      <input className="input" type={type} placeholder={label}
             value={form[key]}
             onChange={(e) => setForm({ ...form, [key]: e.target.value })}
             required={["username","password","password2"].includes(key)} />
    </div>
  );

  return (
    <div className="min-h-screen bg-[var(--bg)] flex items-center justify-center p-4">
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute -top-40 -right-40 w-96 h-96 bg-primary-500/10 rounded-full blur-3xl" />
      </div>

      <motion.div initial={{ opacity: 0, y: 24 }} animate={{ opacity: 1, y: 0 }}
                  className="relative w-full max-w-md">
        <div className="card p-8 shadow-xl">
          <div className="text-center mb-7">
            <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-primary-400 to-primary-600
                            flex items-center justify-center mx-auto mb-3 shadow-lg shadow-primary-500/30">
              <ChefHat size={28} className="text-white" />
            </div>
            <h1 className="text-xl font-bold">{t("register")}</h1>
          </div>

          <form onSubmit={handleSubmit} className="space-y-3">
            <div className="grid grid-cols-2 gap-3">
              {field("first_name", t("firstName"))}
              {field("last_name",  t("lastName"))}
            </div>
            {field("username", t("username"))}
            {field("email",    t("email"), "email")}
            {field("password",  t("password"), "password")}
            {field("password2", t("password") + " (кайтал)", "password")}

            <div>
              <label className="block text-sm font-medium mb-1.5">{t("role")}</label>
              <select className="input"
                      value={form.role}
                      onChange={(e) => setForm({ ...form, role: e.target.value })}>
                <option value="user">{t("user")}</option>
                <option value="admin">{t("admin")}</option>
              </select>
            </div>

            {error && (
              <p className="text-sm text-red-500 bg-red-50 dark:bg-red-900/20
                            border border-red-200 dark:border-red-800 rounded-xl px-4 py-2.5">
                {error}
              </p>
            )}

            <button type="submit" disabled={loading}
                    className="btn-primary w-full flex items-center justify-center gap-2">
              {loading && <Loader2 size={16} className="animate-spin" />}
              {t("register")}
            </button>
          </form>

          <p className="text-center text-sm text-[var(--muted)] mt-5">
            Аккаунт бар болсо{" "}
            <Link to="/login" className="text-primary-500 font-semibold hover:underline">
              {t("login")}
            </Link>
          </p>
        </div>
      </motion.div>
    </div>
  );
}
