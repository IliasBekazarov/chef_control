import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { motion } from "framer-motion";
import { format } from "date-fns";
import { Search, Shield, User } from "lucide-react";
import api from "../api";
import LoadingSpinner from "../components/LoadingSpinner";

export default function UsersPage() {
  const { t } = useTranslation();
  const [users,   setUsers]   = useState([]);
  const [loading, setLoading] = useState(true);
  const [search,  setSearch]  = useState("");

  useEffect(() => {
    api.get("/users/", { params: { search } })
      .then(({ data }) => setUsers(data.results || data))
      .finally(() => setLoading(false));
  }, [search]);

  return (
    <div className="p-4 lg:p-6 space-y-5 animate-fade-in">
      <div>
        <h1 className="text-2xl font-bold">{t("users")}</h1>
        <p className="text-sm text-[var(--muted)]">{users.length} колдонуучу</p>
      </div>

      <div className="card p-4">
        <div className="relative max-w-sm">
          <Search size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-[var(--muted)]" />
          <input className="input pl-9" placeholder={t("search")}
                 value={search} onChange={(e) => setSearch(e.target.value)} />
        </div>
      </div>

      {loading ? (
        <LoadingSpinner text={t("loading")} />
      ) : (
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {users.map((u, i) => (
            <motion.div key={u.id}
              initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.04 }}
              className="card p-4 flex items-center gap-4">
              {/* Avatar */}
              <div className={`w-12 h-12 rounded-full flex items-center justify-center flex-shrink-0
                              text-white font-bold text-lg
                              ${u.is_staff || u.profile?.role === "admin"
                                ? "bg-gradient-to-br from-primary-400 to-primary-600"
                                : "bg-gradient-to-br from-blue-400 to-indigo-500"}`}>
                {(u.first_name || u.username)[0].toUpperCase()}
              </div>

              <div className="flex-1 min-w-0">
                <p className="font-semibold truncate">{u.full_name}</p>
                <p className="text-xs text-[var(--muted)] truncate">{u.email || u.username}</p>
                <div className="flex items-center gap-1.5 mt-1.5">
                  {(u.is_staff || u.profile?.role === "admin") ? (
                    <span className="inline-flex items-center gap-1 text-xs font-semibold
                                     bg-orange-100 text-orange-600 dark:bg-orange-900/30 dark:text-orange-400
                                     px-2 py-0.5 rounded-full">
                      <Shield size={10} /> {t("admin")}
                    </span>
                  ) : (
                    <span className="inline-flex items-center gap-1 text-xs font-semibold
                                     bg-blue-100 text-blue-600 dark:bg-blue-900/30 dark:text-blue-400
                                     px-2 py-0.5 rounded-full">
                      <User size={10} /> {t("user")}
                    </span>
                  )}
                  {u.profile?.location && (
                    <span className="text-xs text-[var(--muted)]">· {u.profile.location}</span>
                  )}
                </div>
              </div>
            </motion.div>
          ))}
        </div>
      )}
    </div>
  );
}
