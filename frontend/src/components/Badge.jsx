import { CheckCircle2, XCircle } from "lucide-react";

export function BadgeOk({ label }) {
  return (
    <span className="badge-ok">
      <CheckCircle2 size={12} /> {label}
    </span>
  );
}

export function BadgeFail({ label }) {
  return (
    <span className="badge-fail">
      <XCircle size={12} /> {label}
    </span>
  );
}
