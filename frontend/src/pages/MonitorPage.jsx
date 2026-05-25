import { useEffect, useState, useRef } from "react";
import { useTranslation } from "react-i18next";
import { motion, AnimatePresence } from "framer-motion";
import { format } from "date-fns";
import {
  CheckCircle2, XCircle, RefreshCw, Wifi, WifiOff,
  ChefHat, Shirt, Clock, AlertTriangle, Activity,
} from "lucide-react";
import api from "../api";

const REFRESH_INTERVAL = 10_000; // 10 секунд

export default function MonitorPage() {
  const { t } = useTranslation();
  const [record,   setRecord]   = useState(null);
  const [loading,  setLoading]  = useState(true);
  const [online,   setOnline]   = useState(true);
  const [lastSync, setLastSync] = useState(null);
  const [countdown, setCountdown] = useState(REFRESH_INTERVAL / 1000);
  const timerRef  = useRef(null);
  const countRef  = useRef(null);

  const fetchLatest = async () => {
    try {
      const { data } = await api.get("/records/", {
        params: { ordering: "-timestamp", page_size: 1 },
      });
      const items = data.results || data;
      setRecord(items[0] || null);
      setOnline(true);
      setLastSync(new Date());
    } catch {
      setOnline(false);
    } finally {
      setLoading(false);
      setCountdown(REFRESH_INTERVAL / 1000);
    }
  };

  useEffect(() => {
    fetchLatest();
    timerRef.current = setInterval(fetchLatest, REFRESH_INTERVAL);
    countRef.current = setInterval(() => {
      setCountdown((c) => (c > 0 ? c - 1 : REFRESH_INTERVAL / 1000));
    }, 1000);
    return () => {
      clearInterval(timerRef.current);
      clearInterval(countRef.current);
    };
  }, []);

  const isCompliant = record?.is_compliant;
  const hasHat      = record?.has_hat;
  const hasApron    = record?.has_apron;

  return (
    <div className="p-4 lg:p-6 space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <Activity size={22} className="text-primary-500" />
            {t("monitor")}
          </h1>
          <p className="text-sm text-[var(--muted)] mt-1">{t("monitorDesc")}</p>
        </div>
        <div className="flex items-center gap-3">
          {/* Online indicator */}
          <div className={`flex items-center gap-1.5 text-sm font-medium px-3 py-1.5 rounded-full
            ${online ? "bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400"
                     : "bg-red-100 text-red-600 dark:bg-red-900/30 dark:text-red-400"}`}>
            {online ? <Wifi size={14} /> : <WifiOff size={14} />}
            {online ? t("online") : t("offline")}
          </div>
          {/* Refresh countdown */}
          <div className="flex items-center gap-1.5 text-xs text-[var(--muted)] bg-[var(--surface)]
                          border border-[var(--border)] px-3 py-1.5 rounded-full">
            <Clock size={12} />
            {countdown}s
          </div>
          <button onClick={fetchLatest}
                  className="btn-ghost flex items-center gap-1.5 text-sm">
            <RefreshCw size={14} /> {t("refresh")}
          </button>
        </div>
      </div>

      {loading ? (
        <div className="flex items-center justify-center h-64">
          <div className="text-center space-y-3">
            <div className="w-12 h-12 border-4 border-primary-500/30 border-t-primary-500
                            rounded-full animate-spin mx-auto" />
            <p className="text-sm text-[var(--muted)]">{t("loading")}</p>
          </div>
        </div>
      ) : !record ? (
        <div className="card p-16 text-center text-[var(--muted)]">
          <Activity size={40} className="mx-auto mb-3 opacity-30" />
          <p className="font-medium">{t("noData")}</p>
          <p className="text-sm mt-1">{t("monitorWaiting")}</p>
        </div>
      ) : (
        <>
          {/* BIG STATUS CARD */}
          <AnimatePresence mode="wait">
            <motion.div
              key={record.id}
              initial={{ opacity: 0, scale: 0.97 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0 }}
              className={`card p-8 border-2 transition-colors ${
                isCompliant
                  ? "border-emerald-400 dark:border-emerald-500"
                  : "border-red-400 dark:border-red-500"
              }`}>
              <div className="flex flex-col sm:flex-row items-center gap-6">
                {/* Status icon */}
                <div className={`w-24 h-24 rounded-3xl flex items-center justify-center flex-shrink-0
                  ${isCompliant
                    ? "bg-emerald-100 dark:bg-emerald-900/30"
                    : "bg-red-100 dark:bg-red-900/30"}`}>
                  {isCompliant
                    ? <CheckCircle2 size={48} className="text-emerald-500" />
                    : <XCircle     size={48} className="text-red-500" />}
                </div>
                <div className="flex-1 text-center sm:text-left">
                  <p className={`text-3xl font-bold ${isCompliant ? "text-emerald-500" : "text-red-500"}`}>
                    {isCompliant ? t("compliantStatus") : t("violationStatus")}
                  </p>
                  <p className="text-[var(--muted)] mt-1 text-sm">
                    {t("lastCheck")}: {format(new Date(record.timestamp), "dd.MM.yyyy HH:mm:ss")}
                  </p>
                  {!isCompliant && record.violations && (
                    <div className="mt-3 flex flex-wrap gap-2 justify-center sm:justify-start">
                      {record.violations.split("|").filter(Boolean).map((v, i) => (
                        <span key={i} className="inline-flex items-center gap-1 text-xs font-semibold
                                                  bg-red-100 text-red-600 dark:bg-red-900/30 dark:text-red-400
                                                  px-2.5 py-1 rounded-full">
                          <AlertTriangle size={10} /> {v.trim()}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
                {/* Frame image */}
                {record.frame_image && (
                  <img src={record.frame_image} alt="frame"
                       className="w-36 h-24 object-cover rounded-2xl border border-[var(--border)] flex-shrink-0" />
                )}
              </div>
            </motion.div>
          </AnimatePresence>

          {/* Hat & Apron cards */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.05 }}
                        className={`card p-6 flex items-center gap-4 border-2 ${
                          hasHat ? "border-emerald-300 dark:border-emerald-600"
                                 : "border-red-300 dark:border-red-600"}`}>
              <div className={`w-14 h-14 rounded-2xl flex items-center justify-center flex-shrink-0
                ${hasHat ? "bg-emerald-100 dark:bg-emerald-900/30"
                         : "bg-red-100 dark:bg-red-900/30"}`}>
                <ChefHat size={28} className={hasHat ? "text-emerald-500" : "text-red-500"} />
              </div>
              <div>
                <p className="font-bold text-lg">{t("hatStatus")}</p>
                <p className={`text-sm font-semibold ${hasHat ? "text-emerald-500" : "text-red-500"}`}>
                  {hasHat ? t("hatOn") : t("hatOff")}
                </p>
                
              </div>
              <div className="ml-auto">
                {hasHat
                  ? <CheckCircle2 size={28} className="text-emerald-400" />
                  : <XCircle     size={28} className="text-red-400" />}
              </div>
            </motion.div>

            <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.1 }}
                        className={`card p-6 flex items-center gap-4 border-2 ${
                          hasApron ? "border-emerald-300 dark:border-emerald-600"
                                   : "border-red-300 dark:border-red-600"}`}>
              <div className={`w-14 h-14 rounded-2xl flex items-center justify-center flex-shrink-0
                ${hasApron ? "bg-emerald-100 dark:bg-emerald-900/30"
                           : "bg-red-100 dark:bg-red-900/30"}`}>
                <Shirt size={28} className={hasApron ? "text-emerald-500" : "text-red-500"} />
              </div>
              <div>
                <p className="font-bold text-lg">{t("apronStatus")}</p>
                <p className={`text-sm font-semibold ${hasApron ? "text-emerald-500" : "text-red-500"}`}>
                  {hasApron ? t("apronOn") : t("apronOff")}
                </p>
                
              </div>
              <div className="ml-auto">
                {hasApron
                  ? <CheckCircle2 size={28} className="text-emerald-400" />
                  : <XCircle     size={28} className="text-red-400" />}
              </div>
            </motion.div>
          </div>

          {/* Last sync */}
          {lastSync && (
            <p className="text-xs text-center text-[var(--muted)]">
              {t("lastSync")}: {format(lastSync, "HH:mm:ss")} · {t("autoRefresh", { sec: REFRESH_INTERVAL / 1000 })}
            </p>
          )}
        </>
      )}
    </div>
  );
}
