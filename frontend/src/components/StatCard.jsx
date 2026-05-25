import { motion } from "framer-motion";
import clsx from "clsx";

export default function StatCard({ icon: Icon, label, value, sub, color = "orange", trend }) {
  const colors = {
    orange:  "from-orange-400 to-primary-500",
    green:   "from-emerald-400 to-teal-500",
    red:     "from-red-400 to-rose-500",
    blue:    "from-blue-400 to-indigo-500",
    purple:  "from-purple-400 to-violet-500",
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      whileHover={{ y: -2 }}
      className="card p-5 flex items-start gap-4 overflow-hidden relative">
      {/* Gradient blob */}
      <div className={clsx(
        "absolute -right-6 -top-6 w-24 h-24 rounded-full opacity-10 bg-gradient-to-br",
        colors[color]
      )} />

      <div className={clsx(
        "w-12 h-12 rounded-2xl flex items-center justify-center flex-shrink-0",
        "bg-gradient-to-br text-white shadow-lg",
        colors[color]
      )}>
        <Icon size={22} />
      </div>

      <div className="flex-1 min-w-0">
        <p className="text-xs font-medium text-[var(--muted)] truncate">{label}</p>
        <p className="text-2xl font-bold mt-0.5 leading-none">{value}</p>
        {sub && <p className="text-xs text-[var(--muted)] mt-1">{sub}</p>}
        {trend !== undefined && (
          <p className={clsx(
            "text-xs font-semibold mt-1",
            trend >= 0 ? "text-emerald-500" : "text-red-500"
          )}>
            {trend >= 0 ? "↑" : "↓"} {Math.abs(trend)}%
          </p>
        )}
      </div>
    </motion.div>
  );
}
