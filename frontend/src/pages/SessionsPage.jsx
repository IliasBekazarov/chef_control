import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { motion } from "framer-motion";
import { format } from "date-fns";
import { FolderOpen, ChevronRight, CheckCircle2, XCircle } from "lucide-react";
import api from "../api";
import LoadingSpinner from "../components/LoadingSpinner";

export default function SessionsPage() {
  const { t } = useTranslation();
  const [sessions, setSessions] = useState([]);
  const [loading, setLoading]   = useState(true);
  const [selected, setSelected] = useState(null);
  const [records,  setRecords]  = useState([]);
  const [recLoading, setRecLoading] = useState(false);

  useEffect(() => {
    api.get("/sessions/", { params: { ordering: "-started_at", page_size: 50 } })
      .then(({ data }) => setSessions(data.results || data))
      .finally(() => setLoading(false));
  }, []);

  const openSession = (s) => {
    setSelected(s);
    setRecLoading(true);
    api.get("/records/", { params: { session: s.id, ordering: "-timestamp", page_size: 100 } })
      .then(({ data }) => setRecords(data.results || data))
      .finally(() => setRecLoading(false));
  };

  return (
    <div className="p-4 lg:p-6 space-y-5 animate-fade-in">
      <div>
        <h1 className="text-2xl font-bold">{t("sessions")}</h1>
        <p className="text-sm text-[var(--muted)]">{sessions.length} сессия</p>
      </div>

      {loading ? (
        <LoadingSpinner text={t("loading")} />
      ) : sessions.length === 0 ? (
        <div className="card p-12 text-center text-[var(--muted)]">{t("noData")}</div>
      ) : (
        <div className="grid gap-3">
          {sessions.map((s, i) => (
            <motion.div key={s.id}
              initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.03 }}
              onClick={() => openSession(s)}
              className="card p-4 flex items-center gap-4 cursor-pointer hover:border-primary-500 transition group">
              <div className="w-11 h-11 rounded-xl bg-blue-100 dark:bg-blue-900/30
                              flex items-center justify-center flex-shrink-0">
                <FolderOpen size={20} className="text-blue-500" />
              </div>
              <div className="flex-1 min-w-0">
                <p className="font-semibold truncate font-mono text-sm">{s.session_id}</p>
                <p className="text-xs text-[var(--muted)] mt-0.5">
                  {s.started_at && format(new Date(s.started_at), "dd.MM.yyyy HH:mm")}
                  {s.created_by_name && ` · ${s.created_by_name}`}
                </p>
              </div>
              <div className="text-right flex-shrink-0">
                <div className="flex items-center gap-3 text-sm">
                  <span className="text-emerald-500 flex items-center gap-1">
                    <CheckCircle2 size={14} /> {s.total_checks - s.violations}
                  </span>
                  <span className="text-red-500 flex items-center gap-1">
                    <XCircle size={14} /> {s.violations}
                  </span>
                  <span className={`font-bold ${s.compliance_rate >= 80 ? "text-emerald-500" : "text-red-500"}`}>
                    {s.compliance_rate}%
                  </span>
                </div>
                <p className="text-xs text-[var(--muted)] mt-0.5">{s.total_checks} текшерүү</p>
              </div>
              <ChevronRight size={16} className="text-[var(--muted)] group-hover:text-primary-500 transition flex-shrink-0" />
            </motion.div>
          ))}
        </div>
      )}

      {/* Session detail drawer */}
      {selected && (
        <div className="fixed inset-0 z-50 flex items-end sm:items-center justify-center p-4 bg-black/60"
             onClick={() => setSelected(null)}>
          <motion.div
            initial={{ opacity: 0, y: 50 }} animate={{ opacity: 1, y: 0 }}
            onClick={(e) => e.stopPropagation()}
            className="card w-full max-w-2xl max-h-[80vh] flex flex-col shadow-2xl">
            {/* Header */}
            <div className="flex items-center gap-3 p-5 border-b border-[var(--border)]">
              <FolderOpen size={20} className="text-blue-500" />
              <div className="flex-1">
                <p className="font-bold font-mono">{selected.session_id}</p>
                <p className="text-xs text-[var(--muted)]">
                  {selected.started_at && format(new Date(selected.started_at), "dd.MM.yyyy HH:mm")}
                </p>
              </div>
              <div className="text-right">
                <p className={`text-xl font-bold ${selected.compliance_rate >= 80 ? "text-emerald-500" : "text-red-500"}`}>
                  {selected.compliance_rate}%
                </p>
                <p className="text-xs text-[var(--muted)]">compliance</p>
              </div>
            </div>

            {/* Records list */}
            <div className="overflow-y-auto flex-1 p-4 space-y-2">
              {recLoading ? (
                <LoadingSpinner text={t("loading")} />
              ) : records.length === 0 ? (
                <p className="text-center text-[var(--muted)] py-8">{t("noData")}</p>
              ) : records.map((rec) => (
                <div key={rec.id}
                     className={`flex items-center gap-3 p-3 rounded-xl border text-sm
                       ${rec.is_compliant
                         ? "border-emerald-200 bg-emerald-50 dark:border-emerald-800 dark:bg-emerald-900/10"
                         : "border-red-200 bg-red-50 dark:border-red-800 dark:bg-red-900/10"}`}>
                  {rec.is_compliant
                    ? <CheckCircle2 size={16} className="text-emerald-500 flex-shrink-0" />
                    : <XCircle size={16} className="text-red-500 flex-shrink-0" />}
                  <span className="font-mono text-xs text-[var(--muted)]">
                    {format(new Date(rec.timestamp), "HH:mm:ss")}
                  </span>
                  <span className="text-xs">
                    Hat: {rec.has_hat ? "✓" : "✗"} · Apron: {rec.has_apron ? "✓" : "✗"}
                  </span>
                  {rec.violations && (
                    <span className="text-xs text-red-500 ml-auto">{rec.violations}</span>
                  )}
                </div>
              ))}
            </div>

            <div className="p-4 border-t border-[var(--border)]">
              <button onClick={() => setSelected(null)} className="btn-primary w-full">Жабуу</button>
            </div>
          </motion.div>
        </div>
      )}
    </div>
  );
}
