import { useEffect, useState, useCallback } from "react";
import { useTranslation } from "react-i18next";
import { motion } from "framer-motion";
import { format } from "date-fns";
import { Search, Filter, ChevronLeft, ChevronRight, RefreshCw, Image } from "lucide-react";
import api from "../api";
import { BadgeOk, BadgeFail } from "../components/Badge";
import LoadingSpinner from "../components/LoadingSpinner";

export default function RecordsPage() {
  const { t } = useTranslation();
  const [records, setRecords]   = useState([]);
  const [loading, setLoading]   = useState(true);
  const [page, setPage]         = useState(1);
  const [count, setCount]       = useState(0);
  const [search, setSearch]     = useState("");
  const [filter, setFilter]     = useState("all"); // all | compliant | violation
  const [selected, setSelected] = useState(null);

  const PAGE_SIZE = 20;

  const load = useCallback(() => {
    setLoading(true);
    const params = { page, ordering: "-timestamp" };
    if (search) params.search = search;
    if (filter === "compliant") params.is_compliant = true;
    if (filter === "violation") params.is_compliant = false;

    api.get("/records/", { params })
      .then(({ data }) => {
        setRecords(data.results || data);
        setCount(data.count || (data.results || data).length);
      })
      .finally(() => setLoading(false));
  }, [page, search, filter]);

  useEffect(() => { load(); }, [load]);

  const totalPages = Math.ceil(count / PAGE_SIZE);

  return (
    <div className="p-4 lg:p-6 space-y-5 animate-fade-in">
      {/* Header */}
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div>
          <h1 className="text-2xl font-bold">{t("records")}</h1>
          <p className="text-sm text-[var(--muted)]">{count} жазуу табылды</p>
        </div>
        <button onClick={load} className="btn-ghost flex items-center gap-2 text-sm">
          <RefreshCw size={15} /> Жаңылоо
        </button>
      </div>

      {/* Filters */}
      <div className="card p-4 flex flex-wrap gap-3 items-center">
        <div className="relative flex-1 min-w-48">
          <Search size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-[var(--muted)]" />
          <input className="input pl-9" placeholder={t("search")}
                 value={search}
                 onChange={(e) => { setSearch(e.target.value); setPage(1); }} />
        </div>
        <div className="flex gap-2">
          {[["all", t("all")], ["compliant", t("compliant")], ["violation", t("violations")]].map(([val, label]) => (
            <button key={val}
                    onClick={() => { setFilter(val); setPage(1); }}
                    className={`px-3 py-2 rounded-xl text-sm font-medium transition ${
                      filter === val
                        ? "bg-primary-500 text-white"
                        : "bg-[var(--bg)] border border-[var(--border)] text-[var(--muted)] hover:border-primary-500"
                    }`}>
              {label}
            </button>
          ))}
        </div>
      </div>

      {/* Table */}
      {loading ? (
        <LoadingSpinner text={t("loading")} />
      ) : records.length === 0 ? (
        <div className="card p-12 text-center text-[var(--muted)]">{t("noData")}</div>
      ) : (
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="card overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-[var(--border)] bg-[var(--bg)]">
                  {[t("timestamp"), t("hatStatus"), t("apronStatus"), "Confidence", t("status"), ""].map((h) => (
                    <th key={h} className="text-left px-4 py-3 text-xs font-semibold text-[var(--muted)] uppercase tracking-wide whitespace-nowrap">
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {records.map((rec, i) => (
                  <motion.tr key={rec.id}
                    initial={{ opacity: 0, x: -10 }} animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: i * 0.02 }}
                    className="border-b border-[var(--border)] hover:bg-[var(--bg)] transition cursor-pointer"
                    onClick={() => setSelected(rec)}>
                    <td className="px-4 py-3 font-mono text-xs whitespace-nowrap">
                      {format(new Date(rec.timestamp), "dd.MM.yyyy HH:mm:ss")}
                    </td>
                    <td className="px-4 py-3">
                      {rec.has_hat
                        ? <BadgeOk label={`✓ ${(rec.hat_confidence * 100).toFixed(0)}%`} />
                        : <BadgeFail label="✗" />}
                    </td>
                    <td className="px-4 py-3">
                      {rec.has_apron
                        ? <BadgeOk label={`✓ ${(rec.apron_confidence * 100).toFixed(0)}%`} />
                        : <BadgeFail label="✗" />}
                    </td>
                    <td className="px-4 py-3 text-[var(--muted)]">
                      Hat {(rec.hat_confidence * 100).toFixed(0)}% / Apron {(rec.apron_confidence * 100).toFixed(0)}%
                    </td>
                    <td className="px-4 py-3">
                      {rec.is_compliant
                        ? <BadgeOk label={t("compliant")} />
                        : <BadgeFail label={t("violation")} />}
                    </td>
                    <td className="px-4 py-3">
                      {rec.frame_image && (
                        <Image size={16} className="text-[var(--muted)]" />
                      )}
                    </td>
                  </motion.tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="flex items-center justify-between px-4 py-3 border-t border-[var(--border)]">
              <p className="text-sm text-[var(--muted)]">
                Бет {page} / {totalPages}
              </p>
              <div className="flex gap-2">
                <button onClick={() => setPage((p) => Math.max(1, p - 1))}
                        disabled={page === 1} className="btn-ghost p-2">
                  <ChevronLeft size={16} />
                </button>
                <button onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                        disabled={page === totalPages} className="btn-ghost p-2">
                  <ChevronRight size={16} />
                </button>
              </div>
            </div>
          )}
        </motion.div>
      )}

      {/* Detail modal */}
      {selected && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60"
             onClick={() => setSelected(null)}>
          <motion.div initial={{ opacity: 0, scale: 0.9 }} animate={{ opacity: 1, scale: 1 }}
                      onClick={(e) => e.stopPropagation()}
                      className="card max-w-md w-full p-6 shadow-2xl">
            <h2 className="font-bold text-lg mb-4">Текшерүү жыйынтыгы</h2>
            <div className="space-y-3 text-sm">
              <div className="flex justify-between">
                <span className="text-[var(--muted)]">{t("timestamp")}</span>
                <span className="font-mono font-medium">
                  {format(new Date(selected.timestamp), "dd.MM.yyyy HH:mm:ss")}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-[var(--muted)]">{t("status")}</span>
                {selected.is_compliant ? <BadgeOk label={t("compliant")} /> : <BadgeFail label={t("violation")} />}
              </div>
              <div className="flex justify-between">
                <span className="text-[var(--muted)]">{t("hatStatus")}</span>
                {selected.has_hat ? <BadgeOk label={`${(selected.hat_confidence*100).toFixed(0)}%`} /> : <BadgeFail label={t("noHat")} />}
              </div>
              <div className="flex justify-between">
                <span className="text-[var(--muted)]">{t("apronStatus")}</span>
                {selected.has_apron ? <BadgeOk label={`${(selected.apron_confidence*100).toFixed(0)}%`} /> : <BadgeFail label={t("noApron")} />}
              </div>
              {selected.violations && (
                <div>
                  <span className="text-[var(--muted)]">Бузуулар:</span>
                  <div className="mt-1.5 flex flex-wrap gap-1.5">
                    {selected.violations_list?.map((v, i) => (
                      <span key={i} className="badge-fail">{v}</span>
                    ))}
                  </div>
                </div>
              )}
              {selected.frame_image && (
                <img src={`/media/${selected.frame_image}`} alt="frame"
                     className="w-full rounded-xl mt-2 border border-[var(--border)]" />
              )}
            </div>
            <button onClick={() => setSelected(null)} className="btn-primary w-full mt-5">Жабуу</button>
          </motion.div>
        </div>
      )}
    </div>
  );
}
