import { motion } from "framer-motion";
import { Loader2 } from "lucide-react";

export default function LoadingSpinner({ text = "" }) {
  return (
    <div className="flex flex-col items-center justify-center py-20 gap-3">
      <motion.div animate={{ rotate: 360 }} transition={{ repeat: Infinity, duration: 1, ease: "linear" }}>
        <Loader2 size={32} className="text-primary-500" />
      </motion.div>
      {text && <p className="text-sm text-[var(--muted)]">{text}</p>}
    </div>
  );
}
