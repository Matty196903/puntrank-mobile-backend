import { Link, useNavigate } from "react-router-dom";
import { UserRound, Crown, Shield, LogOut, FileText, HelpCircle, ExternalLink } from "lucide-react";
import { useAuth } from "@/context/AuthContext";

const PLAN_LABEL = { pro_monthly: "Pro Monthly", pro_annual: "Pro Annual", pro_lifetime: "Pro Lifetime", admin: "Admin", admin_grant: "Pro (granted)" };

export default function AccountPage() {
  const { user, isPro, logout } = useAuth();
  const nav = useNavigate();

  return (
    <div className="fade-up" data-testid="account-page">
      <div className="flex items-center gap-2">
        <UserRound className="w-6 h-6 text-emerald-500" />
        <h1 className="font-display text-4xl font-extrabold uppercase tracking-tight">Account</h1>
      </div>

      <div className="pr-card p-4 mt-4" data-testid="account-profile">
        {user ? (
          <>
            <p className="text-sm font-semibold">{user.name || user.email}</p>
            <p className="text-xs text-zinc-500">{user.email}</p>
            <div className="flex items-center gap-2 mt-2">
              {isPro ? (
                <span data-testid="account-plan" className="px-2.5 py-1 rounded-full text-xs font-bold bg-amber-500/15 text-amber-400 border border-amber-500/30">
                  {PLAN_LABEL[user.pro_plan] || "PRO"}
                </span>
              ) : (
                <span data-testid="account-plan" className="px-2.5 py-1 rounded-full text-xs font-bold bg-zinc-800 text-zinc-400">Free</span>
              )}
              {user.role === "admin" && <span className="px-2.5 py-1 rounded-full text-xs font-bold bg-emerald-500/15 text-emerald-400">ADMIN</span>}
            </div>
          </>
        ) : (
          <>
            <p className="text-sm text-zinc-300">Browsing as guest</p>
            <Link to="/auth" data-testid="account-signin-btn"
              className="inline-block mt-2 px-4 py-2 rounded-full text-xs font-bold bg-emerald-600 hover:bg-emerald-500 text-white transition-colors">
              Sign in / Create account
            </Link>
          </>
        )}
      </div>

      <h2 className="font-display text-2xl font-bold uppercase tracking-tight mt-6 mb-2">Subscription</h2>
      <div className="pr-card p-4">
        {isPro ? (
          <p className="text-sm text-zinc-300">You're on <span className="text-amber-400 font-semibold">{PLAN_LABEL[user?.pro_plan] || "Pro"}</span> — everything is unlocked. 🏇</p>
        ) : (
          <>
            <p className="text-sm text-zinc-400">Unlock all A-Grade plays, full reasoning, every exotic, Ace's quaddie and all PDF reports.</p>
            <Link to="/pricing" data-testid="account-gopro-btn"
              className="inline-flex items-center gap-1.5 mt-3 px-4 py-2 rounded-full text-xs font-bold bg-amber-500 text-zinc-950 hover:bg-amber-400 transition-colors">
              <Crown className="w-4 h-4" /> Go Pro — from A$9.99/mo
            </Link>
          </>
        )}
      </div>

      <h2 className="font-display text-2xl font-bold uppercase tracking-tight mt-6 mb-2">More</h2>
      <div className="pr-card divide-y divide-zinc-800/70">
        <Link to="/guide" data-testid="account-guide-link" className="flex items-center gap-3 p-3.5 text-sm text-zinc-300 hover:text-emerald-400 transition-colors">
          <HelpCircle className="w-4 h-4" /> How PuntRank works (A/B/C grades)
        </Link>
        <Link to="/reports" data-testid="account-reports-link" className="flex items-center gap-3 p-3.5 text-sm text-zinc-300 hover:text-emerald-400 transition-colors">
          <FileText className="w-4 h-4" /> PDF Reports
        </Link>
        {user?.role === "admin" && (
          <Link to="/admin" data-testid="account-admin-link" className="flex items-center gap-3 p-3.5 text-sm text-zinc-300 hover:text-emerald-400 transition-colors">
            <Shield className="w-4 h-4" /> Admin panel
          </Link>
        )}
        <a href="https://www.gamblinghelponline.org.au" target="_blank" rel="noreferrer" data-testid="account-help-link"
          className="flex items-center gap-3 p-3.5 text-sm text-zinc-300 hover:text-emerald-400 transition-colors">
          <ExternalLink className="w-4 h-4" /> Gambling Help Online — 1800 858 858
        </a>
        {user && (
          <button data-testid="account-logout-btn" onClick={async () => { await logout(); nav("/"); }}
            className="flex items-center gap-3 p-3.5 text-sm text-red-400 hover:text-red-300 transition-colors w-full text-left">
            <LogOut className="w-4 h-4" /> Sign out
          </button>
        )}
      </div>

      <p className="text-[11px] text-zinc-600 mt-5 leading-relaxed">
        PuntRank Aus is a probability-ranking tool, not a betting or wagering service. Past performance does not guarantee future results.
        18+ only. Gamble responsibly — chances are you're about to lose.
      </p>
    </div>
  );
}
