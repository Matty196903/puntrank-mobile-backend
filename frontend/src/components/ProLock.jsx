import { Link } from "react-router-dom";
import { Lock } from "lucide-react";

export const ProLock = ({ count, label = "more selections", testid = "pro-lock" }) => (
  <Link to="/pricing" data-testid={testid}
    className="block pr-card p-4 border-amber-500/30 hover:border-amber-500/60 text-center">
    <Lock className="w-5 h-5 text-amber-500 mx-auto mb-1.5" />
    <p className="text-sm font-semibold text-zinc-200">{count > 0 ? `${count} ${label} locked` : `${label}`}</p>
    <p className="text-xs text-amber-400 mt-0.5 font-semibold">Unlock everything with Pro — from A$9.99/mo</p>
  </Link>
);
