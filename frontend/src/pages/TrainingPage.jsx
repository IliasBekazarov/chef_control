import { useEffect, useState, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Play, Square, RefreshCw, Cpu, TrendingUp,
  CheckCircle2, XCircle, Loader2, Brain, ChevronDown,
} from "lucide-react";
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer, ReferenceLine,
} from "recharts";
import api from "../api";

const POLL_INTERVAL = 8000; // 8 сек

const MODELS = [
  { value: "yolov8n.pt", label: "YOLOv8n — Nano (тез, 6 MB)",   desc: "~30 мин · ~70% mAP" },
  { value: "yolov8s.pt", label: "YOLOv8s — Small (сунушталат)", desc: "~60 мин · ~88% mAP", recommended: true },
  { value: "yolov8m.pt", label: "YOLOv8m — Medium (так, жай)",   desc: "~2 саат · ~92% mAP" },
];

const EPOCH_OPTIONS = [50, 75, 100, 150];

function gradeColor(map50) {
  if (map50 >= 0.90) return "text-emerald-500";
  if (map50 >= 0.75) return "text-amber-500";
  return "text-red-500";
}

function gradeLabel(map50) {
  if (map50 >= 0.90) return "Мыкты";
  if (map50 >= 0.75) return "Жакшы";
  if (map50 > 0)     return "Жетишсиз";
  return "—";
}

function StateChip({ state }) {
  const map = {
    idle:     { label: "Бош",           cls: "bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-400" },
    training: { label: "Тренинг жүрөт", cls: "bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400", pulse: true },
    done:     { label: "Бүттү",          cls: "bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400" },
    stopped:  { label: "Токтотулду",     cls: "bg-red-100 text-red-600 dark:bg-red-900/30 dark:text-red-400" },
    error:    { label: "Ката",           cls: "bg-red-100 text-red-600 dark:bg-red-900/30 dark:text-red-400" },
  };
  const cfg = map[state] || map.idle;
  return (
    <span className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-sm font-medium ${cfg.cls}`}>
      {cfg.pulse && (
        <span className="relative flex h-2 w-2">
          <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-amber-400 opacity-75" />
          <span className="relative inline-flex rounded-full h-2 w-2 bg-amber-500" />
        </span>
      )}
      {cfg.label}
    </span>
  );
}

export default function TrainingPage() {
  const [status,     setStatus]     = useState(null);
  const [loading,    setLoading]    = useState(true);
  const [starting,   setStarting]   = useState(false);
  const [stopping,   setStopping]   = useState(false);
  const [feedback,   setFeedback]   = useState(null);
  const [model,      setModel]      = useState("yolov8s.pt");
  const [epochs,     setEpochs]     = useState(100);
  const [showConfig, setShowConfig] = useState(false);
  const pollRef = useRef(null);

  const fetchStatus = async (quiet = false) => {
    try {
      const { data } = await api.get("/training/status/");
      setStatus(data);
    } catch {
      if (!quiet) setStatus(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStatus();
    pollRef.current = setInterval(() => fetchStatus(true), POLL_INTERVAL);
    return () => clearInterval(pollRef.current);
  }, []);

  const start = async () => {
    setStarting(true); setFeedback(null);
    try {
      await api.post("/training/start/", { model, epochs, device: "mps" });
      setFeedback({ ok: true, msg: "Тренинг башталды 🚀 — бет автоматтык жаңыланат" });
      setTimeout(() => fetchStatus(), 2000);
    } catch (e) {
      setFeedback({ ok: false, msg: e?.response?.data?.error || "Тренинг баштоодо ката" });
    } finally {
      setStarting(false);
      setTimeout(() => setFeedback(null), 6000);
    }
  };

  const stop = async () => {
    setStopping(true);
    try {
      await api.post("/training/stop/");
      setFeedback({ ok: true, msg: "Тренинг токтотулду" });
      setTimeout(() => fetchStatus(), 1000);
    } catch (e) {
      setFeedback({ ok: false, msg: e?.response?.data?.error || "Токтотуудо ката" });
    } finally {
      setStopping(false);
      setTimeout(() => setFeedback(null), 4000);
    }
  };

  const isTraining = status?.state === "training";
  const isDone     = status?.state === "done";
  const progress   = status && status.epochs_total > 0
    ? Math.round((status.epoch / status.epochs_total) * 100)
    : 0;

  return (
    <div className="p-4 lg:p-6 space-y-6 animate-fade-in max-w-4xl">
      {/* Header */}
      <div className="flex items-start justify-between gap-4 flex-wrap">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <Brain size={22} className="text-primary-500" />
            ML Тренинг
          </h1>
          <p className="text-sm text-[var(--muted)] mt-1">
            YOLOv8 моделин chef hat + apron dataset'ке окутуу
          </p>
        </div>
        {status && <StateChip state={status.state} />}
      </div>

      {loading ? (
        <div className="card p-12 flex items-center justify-center gap-3 text-[var(--muted)]">
          <Loader2 size={20} className="animate-spin" />
          <span>Тренинг абалы жүктөлүүдө…</span>
        </div>
      ) : (
        <>
          {/* Current model KPI */}
          {status && (
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
              {[
                { label: "Учурдагы Epoch",   value: `${status.epoch} / ${status.epochs_total}`, icon: Cpu },
                { label: "Учурдагы mAP50",   value: status.map50 > 0 ? `${(status.map50 * 100).toFixed(1)}%` : "—", icon: TrendingUp },
                { label: "Эң жакшы mAP50",   value: status.map50_best > 0 ? `${(status.map50_best * 100).toFixed(1)}%` : "—", icon: CheckCircle2 },
                { label: "Баа",              value: gradeLabel(status.map50_best), icon: status.map50_best >= 0.75 ? CheckCircle2 : XCircle },
              ].map(({ label, value, icon: Icon }) => (
                <div key={label} className="card p-4">
                  <p className="text-xs text-[var(--muted)] mb-1">{label}</p>
                  <p className={`text-xl font-bold ${label === "Баа" ? gradeColor(status.map50_best) : ""}`}>
                    {value}
                  </p>
                </div>
              ))}
            </div>
          )}

          {/* Progress bar */}
          {isTraining && (
            <motion.div className="card p-5 space-y-3"
              initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }}>
              <div className="flex items-center justify-between text-sm">
                <span className="font-medium">Прогресс</span>
                <span className="text-[var(--muted)]">{progress}%</span>
              </div>
              <div className="w-full h-3 bg-[var(--border)] rounded-full overflow-hidden">
                <motion.div
                  className="h-full bg-gradient-to-r from-primary-400 to-primary-600 rounded-full"
                  initial={{ width: 0 }}
                  animate={{ width: `${progress}%` }}
                  transition={{ duration: 0.6 }}
                />
              </div>
              <p className="text-xs text-[var(--muted)]">
                Epoch {status.epoch} / {status.epochs_total} · mAP50: {(status.map50 * 100).toFixed(1)}%
              </p>
            </motion.div>
          )}

          {/* Chart */}
          {status?.history?.length > 1 && (
            <motion.div className="card p-5"
              initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }}>
              <h2 className="font-semibold mb-4">mAP50 прогресси</h2>
              <ResponsiveContainer width="100%" height={200}>
                <LineChart data={status.history} margin={{ top: 5, right: 10, left: -20, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
                  <XAxis dataKey="epoch" tick={{ fontSize: 10 }} />
                  <YAxis domain={[0, 1]} tickFormatter={(v) => `${(v * 100).toFixed(0)}%`}
                         tick={{ fontSize: 10 }} />
                  <Tooltip formatter={(v) => `${(v * 100).toFixed(1)}%`} />
                  <ReferenceLine y={0.75} stroke="#f97316" strokeDasharray="4 4"
                                 label={{ value: "75%", position: "right", fontSize: 10 }} />
                  <ReferenceLine y={0.90} stroke="#10b981" strokeDasharray="4 4"
                                 label={{ value: "90%", position: "right", fontSize: 10 }} />
                  <Line type="monotone" dataKey="map50" stroke="#3b82f6"
                        dot={false} strokeWidth={2} name="mAP50" />
                </LineChart>
              </ResponsiveContainer>
            </motion.div>
          )}

          {/* Config + Controls */}
          {!isTraining && (
            <motion.div className="card p-5 space-y-4"
              initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }}>
              <button
                onClick={() => setShowConfig(!showConfig)}
                className="flex items-center gap-2 text-sm font-medium text-[var(--muted)] hover:text-[var(--text)] transition"
              >
                <ChevronDown size={14} className={`transition-transform ${showConfig ? "rotate-180" : ""}`} />
                Тренинг параметрлери
              </button>

              <AnimatePresence>
                {showConfig && (
                  <motion.div
                    initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: "auto" }}
                    exit={{ opacity: 0, height: 0 }} className="space-y-4 overflow-hidden"
                  >
                    {/* Model select */}
                    <div>
                      <label className="block text-sm font-medium mb-2">Базалык модел</label>
                      <div className="space-y-2">
                        {MODELS.map((m) => (
                          <label key={m.value}
                            className={`flex items-start gap-3 p-3 rounded-xl border cursor-pointer transition
                              ${model === m.value
                                ? "border-primary-500 bg-primary-50 dark:bg-primary-900/20"
                                : "border-[var(--border)] hover:border-primary-400"}`}>
                            <input type="radio" name="model" value={m.value}
                                   checked={model === m.value}
                                   onChange={() => setModel(m.value)}
                                   className="mt-0.5 accent-primary-500" />
                            <div>
                              <p className="text-sm font-medium">
                                {m.label}
                                {m.recommended && (
                                  <span className="ml-2 text-xs bg-primary-100 text-primary-600
                                                   dark:bg-primary-900/30 px-2 py-0.5 rounded-full">
                                    Сунушталат
                                  </span>
                                )}
                              </p>
                              <p className="text-xs text-[var(--muted)] mt-0.5">{m.desc}</p>
                            </div>
                          </label>
                        ))}
                      </div>
                    </div>

                    {/* Epochs */}
                    <div>
                      <label className="block text-sm font-medium mb-2">Эпох саны</label>
                      <div className="grid grid-cols-4 gap-2">
                        {EPOCH_OPTIONS.map((e) => (
                          <button key={e} onClick={() => setEpochs(e)}
                            className={`py-2 rounded-xl text-sm font-medium border transition
                              ${epochs === e
                                ? "border-primary-500 bg-primary-50 dark:bg-primary-900/20 text-primary-600"
                                : "border-[var(--border)] text-[var(--muted)] hover:border-primary-400"}`}>
                            {e}
                          </button>
                        ))}
                      </div>
                    </div>

                    <div className="flex items-center gap-2 text-xs text-[var(--muted)]
                                    bg-[var(--surface)] border border-[var(--border)] rounded-xl px-3 py-2.5">
                      <Cpu size={13} /> Device: Apple Silicon MPS GPU — CPU'дан 6x тезирээк
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
            </motion.div>
          )}

          {/* Error */}
          {status?.error && (
            <div className="card p-4 border-red-300 dark:border-red-700 text-sm text-red-600">
              <p className="font-medium">Ката:</p>
              <p className="font-mono text-xs mt-1">{status.error}</p>
            </div>
          )}

          {/* Feedback */}
          <AnimatePresence>
            {feedback && (
              <motion.div
                key="fb"
                initial={{ opacity: 0, y: -4 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }}
                className={`flex items-center gap-2 text-sm rounded-xl px-4 py-3 border
                  ${feedback.ok
                    ? "text-emerald-600 bg-emerald-50 dark:bg-emerald-900/20 border-emerald-200 dark:border-emerald-800"
                    : "text-red-600 bg-red-50 dark:bg-red-900/20 border-red-200 dark:border-red-800"}`}
              >
                {feedback.ok ? <CheckCircle2 size={15} /> : <XCircle size={15} />}
                {feedback.msg}
              </motion.div>
            )}
          </AnimatePresence>

          {/* Action buttons */}
          <div className="flex gap-3">
            {!isTraining ? (
              <button onClick={start} disabled={starting}
                      className="btn-primary flex items-center gap-2 flex-1">
                {starting ? <Loader2 size={16} className="animate-spin" /> : <Play size={16} />}
                Тренинг баштоо
              </button>
            ) : (
              <button onClick={stop} disabled={stopping}
                      className="flex items-center gap-2 flex-1 px-4 py-2.5 rounded-xl
                                 bg-red-500 hover:bg-red-600 text-white font-medium transition">
                {stopping ? <Loader2 size={16} className="animate-spin" /> : <Square size={16} />}
                Токтотуу
              </button>
            )}
            <button onClick={() => fetchStatus()}
                    className="btn-ghost flex items-center gap-2 px-4">
              <RefreshCw size={15} /> Жаңылоо
            </button>
          </div>

          {isDone && status.map50_best > 0 && (
            <motion.div
              initial={{ opacity: 0, scale: 0.97 }} animate={{ opacity: 1, scale: 1 }}
              className="card p-5 border-emerald-300 dark:border-emerald-700 text-center space-y-2">
              <p className="text-2xl">🎉</p>
              <p className="font-bold text-lg">Тренинг ийгиликтүү бүттү!</p>
              <p className={`text-3xl font-bold ${gradeColor(status.map50_best)}`}>
                {(status.map50_best * 100).toFixed(1)}% mAP50
              </p>
              <p className="text-sm text-[var(--muted)]">
                Модел автоматтык <code className="bg-[var(--border)] px-1 rounded">models/chef_detector.pt</code>'ка сакталды
              </p>
            </motion.div>
          )}
        </>
      )}
    </div>
  );
}
