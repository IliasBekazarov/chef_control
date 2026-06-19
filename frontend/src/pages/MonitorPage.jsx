import { useEffect, useState, useRef, useCallback } from "react";
import { useTranslation } from "react-i18next";
import { motion, AnimatePresence } from "framer-motion";
import { format } from "date-fns";
import {
  CheckCircle2, XCircle, Wifi, WifiOff,
  ChefHat, Shirt, AlertTriangle, Activity, Radio,
} from "lucide-react";
import api from "../api";

// Dev: ws://localhost:8000  |  Prod: VITE_WS_URL=wss://your-backend.railway.app
const _wsBase = import.meta.env.VITE_WS_URL ?? "ws://localhost:8000";
const WS_URL  = `${_wsBase}/ws/monitor/`;
const RECONNECT_DELAY_MS = 3000;
const POLL_INTERVAL_MS   = 10_000;

function useMonitorSocket() {
  const [record,   setRecord]   = useState(null);
  const [wsState,  setWsState]  = useState("connecting");
  const [lastSync, setLastSync] = useState(null);
  const wsRef     = useRef(null);
  const retryRef  = useRef(null);
  const pollRef   = useRef(null);
  const unmounted = useRef(false);

  // REST'тен акыркы record'ду тартат — ар 10с polling + баштоо
  const fetchLatest = useCallback(async () => {
    try {
      const { data } = await api.get("/records/", {
        params: { ordering: "-timestamp", page_size: 1 },
      });
      const items = data.results ?? data;
      if (unmounted.current || !items[0]) return;
      setRecord(items[0]);
      setLastSync(new Date());
    } catch { /* silent */ }
  }, []);

  const connectWs = useCallback(() => {
    if (unmounted.current) return;
    const token = localStorage.getItem("access") ||
                  localStorage.getItem("access_token") ||
                  JSON.parse(localStorage.getItem("auth") || "{}").access;
    if (!token) { setWsState("closed"); return; }

    const ws = new WebSocket(`${WS_URL}?token=${token}`);
    wsRef.current = ws;

    ws.onopen = () => {
      if (!unmounted.current) setWsState("open");
    };
    ws.onclose = () => {
      if (unmounted.current) return;
      setWsState("closed");
      retryRef.current = setTimeout(connectWs, RECONNECT_DELAY_MS);
    };
    ws.onerror = () => ws.close();
    ws.onmessage = (e) => {
      try {
        const data = JSON.parse(e.data);
        if (!unmounted.current) { setRecord(data); setLastSync(new Date()); }
      } catch { /* ignore */ }
    };
  }, []);

  useEffect(() => {
    unmounted.current = false;

    // Баштапкы маалымат
    fetchLatest();

    // WebSocket туташуу
    connectWs();

    // Ар 10 секунтта polling (WebSocket иштебегенде резерв)
    pollRef.current = setInterval(fetchLatest, POLL_INTERVAL_MS);

    return () => {
      unmounted.current = true;
      clearTimeout(retryRef.current);
      clearInterval(pollRef.current);
      wsRef.current?.close();
    };
  }, []);

  return { record, wsState, lastSync };
}

// ─── Sub-components ──────────────────────────────────────────────────────────
function LiveBadge({ state }) {
  if (state === "open") {
    return (
      <div className="flex items-center gap-1.5 text-sm font-medium px-3 py-1.5 rounded-full
                      bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400">
        <span className="relative flex h-2 w-2">
          <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75" />
          <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500" />
        </span>
        LIVE
      </div>
    );
  }
  if (state === "connecting") {
    return (
      <div className="flex items-center gap-1.5 text-sm font-medium px-3 py-1.5 rounded-full
                      bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400">
        <Radio size={13} className="animate-pulse" />
        Байланышуу…
      </div>
    );
  }
  return (
    <div className="flex items-center gap-1.5 text-sm font-medium px-3 py-1.5 rounded-full
                    bg-red-100 text-red-600 dark:bg-red-900/30 dark:text-red-400">
      <WifiOff size={13} /> Офлайн
    </div>
  );
}

function PPECard({ ok, icon: Icon, label, onLabel, offLabel, delay }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }}
      transition={{ delay }}
      className={`card p-6 flex items-center gap-4 border-2 ${
        ok ? "border-emerald-300 dark:border-emerald-600"
           : "border-red-300 dark:border-red-600"}`}
    >
      <div className={`w-14 h-14 rounded-2xl flex items-center justify-center flex-shrink-0
        ${ok ? "bg-emerald-100 dark:bg-emerald-900/30"
             : "bg-red-100 dark:bg-red-900/30"}`}>
        <Icon size={28} className={ok ? "text-emerald-500" : "text-red-500"} />
      </div>
      <div>
        <p className="font-bold text-lg">{label}</p>
        <p className={`text-sm font-semibold ${ok ? "text-emerald-500" : "text-red-500"}`}>
          {ok ? onLabel : offLabel}
        </p>
      </div>
      <div className="ml-auto">
        {ok ? <CheckCircle2 size={28} className="text-emerald-400" />
            : <XCircle     size={28} className="text-red-400" />}
      </div>
    </motion.div>
  );
}

// ─── Page ─────────────────────────────────────────────────────────────────────
export default function MonitorPage() {
  const { t }                        = useTranslation();
  const { record, wsState, lastSync } = useMonitorSocket();

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
        <LiveBadge state={wsState} />
      </div>

      {!record ? (
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
              }`}
            >
              <div className="flex flex-col sm:flex-row items-center gap-6">
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
                {record.frame_image && (
                  <img src={record.frame_image} alt="frame"
                       className="w-36 h-24 object-cover rounded-2xl border border-[var(--border)] flex-shrink-0" />
                )}
              </div>
            </motion.div>
          </AnimatePresence>

          {/* Hat & Apron */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <PPECard ok={hasHat}   icon={ChefHat} label={t("hatStatus")}
                     onLabel={t("hatOn")} offLabel={t("hatOff")} delay={0.05} />
            <PPECard ok={hasApron} icon={Shirt}   label={t("apronStatus")}
                     onLabel={t("apronOn")} offLabel={t("apronOff")} delay={0.1} />
          </div>

          {/* Last sync */}
          {lastSync && (
            <p className="text-xs text-center text-[var(--muted)]">
              {t("lastSync")}: {format(lastSync, "HH:mm:ss")}
              {wsState === "open"
                ? " · Real-time (WebSocket)"
                : " · Акыркы кэш"}
            </p>
          )}
        </>
      )}
    </div>
  );
}
