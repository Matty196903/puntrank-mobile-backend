import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Check, Crown } from "lucide-react";
import { toast } from "sonner";
import api, { fmtErr } from "@/lib/api";
import { useAuth } from "@/context/AuthContext";

const FEATURES = ["Every runner's reasoning & confidence", "All A-Grade bets + cross-race multis",
  "Full exotics: trifecta, first four, quaddie", "Ace's complete Winners, Places & Quaddies",
  "All PDF reports & scorecards", "Works on web AND the PuntRank mobile app"];

export default function PricingPage() {
  const [plans, setPlans] = useState([]);
  const [busy, setBusy] = useState(null);
  const { user, isPro } = useAuth();
  const nav = useNavigate();

  useEffect(() => { api.get("/payments/plans").then((r) => setPlans(r.data.plans)); }, []);

  const checkout = async (lookup_key) => {
    if (!user) { toast("Sign in first to upgrade"); nav("/auth?next=/pricing"); return; }
    setBusy(lookup_key);
    try {
      const { data } = await api.post("/payments/checkout", { lookup_key, origin_url: window.location.origin });
      window.location.href = data.checkout_url;
    } catch (e) {
      toast.error(fmtErr(e.response?.data?.detail));
      setBusy(null);
    }
  };

  return (
    <div className="fade-up max-w-2xl mx-auto" data-testid="pricing-page">
      <div className="text-center">
        <Crown className="w-8 h-8 text-amber-500 mx-auto" />
        <h1 className="font-display text-4xl font-extrabold uppercase tracking-tight mt-2">PuntRank Pro</h1>
        <p className="text-sm text-zinc-400 mt-1">One subscription — Pro unlocks on web and mobile together.</p>
        {isPro && <p className="mt-3 text-sm font-semibold text-emerald-400" data-testid="already-pro-msg">You're already Pro — everything is unlocked. 🏆</p>}
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 mt-6">
        {plans.map((p) => (
          <div key={p.lookup_key} className={`pr-card p-4 flex flex-col ${p.lookup_key === "pro_annual" ? "border-amber-500/50 shadow-[0_0_20px_rgba(245,158,11,0.12)]" : ""}`} data-testid={`plan-card-${p.lookup_key}`}>
            {p.lookup_key === "pro_annual" && <span className="text-[10px] font-bold text-amber-400 uppercase tracking-widest mb-1">Best value</span>}
            <p className="font-display text-xl font-bold uppercase">{p.label}</p>
            <p className="font-mono-num text-2xl font-bold text-emerald-400 mt-1">{p.price}<span className="text-xs text-zinc-500 font-normal ml-1">{p.period}</span></p>
            <p className="text-xs text-zinc-500 mt-1 flex-1">{p.note}</p>
            <button data-testid={`checkout-btn-${p.lookup_key}`} onClick={() => checkout(p.lookup_key)} disabled={busy !== null || isPro}
              className="mt-3 px-3 py-2 rounded-full text-xs font-bold bg-amber-500 text-zinc-950 hover:bg-amber-400 transition-colors disabled:opacity-50">
              {busy === p.lookup_key ? "Redirecting…" : "Choose plan"}
            </button>
          </div>
        ))}
      </div>

      <div className="pr-card p-5 mt-5">
        <p className="font-semibold text-sm mb-3">Everything in Pro:</p>
        <ul className="space-y-2">
          {FEATURES.map((f) => (
            <li key={f} className="flex items-start gap-2 text-sm text-zinc-300">
              <Check className="w-4 h-4 text-emerald-400 mt-0.5 shrink-0" /> {f}
            </li>
          ))}
        </ul>
      </div>
      <p className="text-[11px] text-zinc-600 text-center mt-4">Secure checkout by Stripe. Prices in AUD incl. applicable taxes. Cancel recurring plans anytime. 18+ only — gamble responsibly.</p>
    </div>
  );
}
