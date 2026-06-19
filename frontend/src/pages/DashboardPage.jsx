import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { motion } from "framer-motion";
import {
  AreaChart, Area, BarChart, Bar, XAxis, YAxis,
  Tooltip, ResponsiveContainer, CartesianGrid, PieChart, Pie, Cell, Legend,
} from "recharts";
import {
  ClipboardCheck, AlertTriangle, TrendingUp,
  FolderOpen, Users, CalendarCheck, FileDown, Loader2,
} from "lucide-react";
import api from "../api";
import StatCard from "../components/StatCard";
import LoadingSpinner from "../components/LoadingSpinner";

const COLORS = ["#f97316", "#ef4444", "#3b82f6", "#8b5cf6", "#10b981"];

function downloadBlob(blob, filename) {
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url; a.download = filename; a.click();
  URL.revokeObjectURL(url);
}

export default function DashboardPage() {
  const { t }         = useTranslation();
  const [stats,       setStats]      = useState(null);
  const [loading,     setLoading]    = useState(true);
  const [pdfLoading,  setPdfLoading] = useState(false);

  useEffect(() => {
    api.get("/dashboard/")
      .then(({ data }) => setStats(data))
      .finally(() => setLoading(false));
  }, []);

  const downloadPdf = async () => {
    setPdfLoading(true);
    try {
      const today = new Date().toISOString().slice(0, 10);
      const resp  = await api.get("/reports/pdf/range/", {
        params:       { date_to: today },
        responseType: "blob",
      });
      downloadBlob(resp.data, `chef_report_${today}.pdf`);
    } finally {
      setPdfLoading(false);
    }
  };

  if (loading) return <LoadingSpinner text={t("loading")} />;
  if (!stats)  return null;

  const pieData = [
    { name: t("compliant"),  value: stats.total_checks - stats.total_violations },
    { name: t("violations"), value: stats.total_violations },
  ];

  return (
    <div className="p-4 lg:p-6 space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex items-start justify-between gap-4 flex-wrap">
        <div>
          <h1 className="text-2xl font-bold">{t("dashboard")}</h1>
          <p className="text-sm text-[var(--muted)] mt-1">{t("appDesc")}</p>
        </div>
        <button
          onClick={downloadPdf}
          disabled={pdfLoading}
          className="btn-secondary flex items-center gap-2 flex-shrink-0"
        >
          {pdfLoading ? <Loader2 size={15} className="animate-spin" /> : <FileDown size={15} />}
          PDF отчет
        </button>
      </div>

      {/* Stat cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard icon={ClipboardCheck}  label={t("totalChecks")}
                  value={stats.total_checks.toLocaleString()} color="orange" />
        <StatCard icon={AlertTriangle}   label={t("violations")}
                  value={stats.total_violations.toLocaleString()} color="red" />
        <StatCard icon={TrendingUp}      label={t("complianceRate")}
                  value={`${stats.compliance_rate}%`} color="green" />
        <StatCard icon={FolderOpen}      label={t("totalSessions")}
                  value={stats.total_sessions.toLocaleString()} color="blue" />
      </div>

      {/* Today row */}
      <div className="grid grid-cols-2 lg:grid-cols-3 gap-4">
        <StatCard icon={CalendarCheck} label={t("todayChecks")}
                  value={stats.today_checks} color="purple" />
        <StatCard icon={AlertTriangle} label={t("todayViol")}
                  value={stats.today_violations} color="red" />
        <StatCard icon={Users}         label={t("activeUsers")}
                  value={stats.active_users} color="blue" />
      </div>

      {/* Charts row */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Area chart — 7 day trend */}
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}
                    className="card p-5 lg:col-span-2">
          <h2 className="font-semibold mb-4">{t("weeklyTrend")}</h2>
          <ResponsiveContainer width="100%" height={220}>
            <AreaChart data={stats.weekly_trend} margin={{ top: 5, right: 10, left: -20, bottom: 0 }}>
              <defs>
                <linearGradient id="gradC" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%"  stopColor="#10b981" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="#10b981" stopOpacity={0} />
                </linearGradient>
                <linearGradient id="gradV" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%"  stopColor="#ef4444" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="#ef4444" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
              <XAxis dataKey="date" tick={{ fontSize: 11 }} stroke="var(--muted)" />
              <YAxis tick={{ fontSize: 11 }} stroke="var(--muted)" />
              <Tooltip
                contentStyle={{
                  background: "var(--surface)", border: "1px solid var(--border)",
                  borderRadius: 12, fontSize: 12,
                }} />
              <Area type="monotone" dataKey="compliant"  stroke="#10b981" strokeWidth={2}
                    fill="url(#gradC)" name={t("compliant")} />
              <Area type="monotone" dataKey="violations" stroke="#ef4444" strokeWidth={2}
                    fill="url(#gradV)" name={t("violations")} />
            </AreaChart>
          </ResponsiveContainer>
        </motion.div>

        {/* Pie chart — compliance */}
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}
                    className="card p-5 flex flex-col">
          <h2 className="font-semibold mb-4">Compliance</h2>
          <div className="flex-1 flex items-center justify-center">
            <ResponsiveContainer width="100%" height={200}>
              <PieChart>
                <Pie data={pieData} cx="50%" cy="50%" innerRadius={55} outerRadius={80}
                     paddingAngle={4} dataKey="value">
                  {pieData.map((_, i) => (
                    <Cell key={i} fill={i === 0 ? "#10b981" : "#ef4444"} />
                  ))}
                </Pie>
                <Legend iconType="circle" iconSize={10} wrapperStyle={{ fontSize: 12 }} />
                <Tooltip contentStyle={{
                  background: "var(--surface)", border: "1px solid var(--border)",
                  borderRadius: 12, fontSize: 12,
                }} />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </motion.div>
      </div>

      {/* Top violations bar */}
      {stats.top_violations.length > 0 && (
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}
                    className="card p-5">
          <h2 className="font-semibold mb-4">{t("topViolations")}</h2>
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={stats.top_violations} layout="vertical"
                      margin={{ top: 0, right: 20, left: 80, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" horizontal={false} />
              <XAxis type="number" tick={{ fontSize: 11 }} stroke="var(--muted)" />
              <YAxis type="category" dataKey="name" tick={{ fontSize: 11 }} stroke="var(--muted)" width={80} />
              <Tooltip contentStyle={{
                background: "var(--surface)", border: "1px solid var(--border)",
                borderRadius: 12, fontSize: 12,
              }} />
              <Bar dataKey="count" radius={[0, 6, 6, 0]}>
                {stats.top_violations.map((_, i) => (
                  <Cell key={i} fill={COLORS[i % COLORS.length]} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </motion.div>
      )}
    </div>
  );
}
