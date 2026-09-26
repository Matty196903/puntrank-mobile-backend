import { Link, useLocation, useNavigate } from "react-router-dom";
import { CalendarDays, Trophy, TrendingDown, BarChart3, Crown, FileText, LogOut, UserRound, Shield, Ticket, HelpCircle } from "lucide-react";
import { useAuth } from "@/context/AuthContext";
import { useSlip } from "@/context/SlipContext";
import { BetSlipDrawer } from "@/components/BetSlipDrawer";
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from "@/components/ui/dropdown-menu";

const NAV = [
  { to: "/", label: "Meetings", icon: CalendarDays, testid: "nav-meetings" },
  { to: "/aces", label: "Ace's", icon: Trophy, testid: "nav-aces" },
  { to: "/best-bets", label: "A-Grade", icon: Crown, testid: "nav-best-bets" },
  { to: "/plunges", label: "Plunges", icon: TrendingDown, testid: "nav-plunges" },
  { to: "/results", label: "Results", icon: BarChart3, testid: "nav-results" },
];

export const Layout = ({ children }) => {
  const { user, isPro, logout } = useAuth();
  const { pins, setOpen } = useSlip();
  const loc = useLocation();
  const nav = useNavigate();

  return (
    <div className="min-h-screen flex flex-col bg-[#0A0D0E]">
      <header className="sticky top-0 z-40 backdrop-blur-md bg-[#0A0D0E]/85 border-b border-zinc-800/80">
        <div className="max-w-5xl mx-auto flex items-center justify-between h-14 px-4">
          <Link to="/" data-testid="logo-link" className="flex items-center gap-2">
            <span className="font-display text-2xl font-extrabold uppercase tracking-tight">
              Punt<span className="text-emerald-500">Rank</span>
              <span className="text-amber-500 ml-1 text-sm align-top font-bold">AUS</span>
            </span>
          </Link>
          <div className="flex items-center gap-2">
            <Link to="/guide" data-testid="nav-guide"
              className={`p-2 rounded-full hover:bg-zinc-800/70 transition-colors ${loc.pathname === "/guide" ? "text-emerald-400" : "text-zinc-400"}`}>
              <HelpCircle className="w-5 h-5" />
            </Link>
            <Link to="/reports" data-testid="nav-reports"
              className={`p-2 rounded-full hover:bg-zinc-800/70 transition-colors ${loc.pathname === "/reports" ? "text-emerald-400" : "text-zinc-400"}`}>
              <FileText className="w-5 h-5" />
            </Link>
            {isPro ? (
              <span data-testid="pro-badge" className="px-2.5 py-1 rounded-full text-xs font-bold bg-amber-500/15 text-amber-400 border border-amber-500/30">PRO</span>
            ) : (
              <Link to="/pricing" data-testid="upgrade-btn"
                className="px-3 py-1.5 rounded-full text-xs font-bold bg-amber-500 text-zinc-950 hover:bg-amber-400 transition-colors">
                Go Pro
              </Link>
            )}
            {user ? (
              <DropdownMenu>
                <DropdownMenuTrigger data-testid="user-menu-btn" className="p-2 rounded-full hover:bg-zinc-800/70 text-zinc-300">
                  <UserRound className="w-5 h-5" />
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end" className="bg-[#121719] border-zinc-800 text-zinc-200">
                  <DropdownMenuItem disabled className="text-xs text-zinc-500">{user.email}</DropdownMenuItem>
                  {user.role === "admin" && (
                    <DropdownMenuItem data-testid="menu-admin" onClick={() => nav("/admin")}>
                      <Shield className="w-4 h-4 mr-2" /> Admin panel
                    </DropdownMenuItem>
                  )}
                  <DropdownMenuItem data-testid="menu-logout" onClick={logout}>
                    <LogOut className="w-4 h-4 mr-2" /> Sign out
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
            ) : (
              <Link to="/auth" data-testid="login-link"
                className="px-3 py-1.5 rounded-full text-xs font-semibold border border-zinc-700 text-zinc-300 hover:border-emerald-500/60 transition-colors">
                Sign in
              </Link>
            )}
          </div>
        </div>
      </header>

      <main className="flex-1 max-w-5xl w-full mx-auto px-4 py-5 pb-32">{children}</main>

      <button data-testid="bet-slip-fab" onClick={() => setOpen(true)}
        className="fixed bottom-20 right-4 z-40 flex items-center gap-2 px-4 h-11 rounded-full bg-emerald-600 hover:bg-emerald-500 text-white font-semibold shadow-[0_0_20px_rgba(16,185,129,0.35)] transition-colors">
        <Ticket className="w-5 h-5" />
        <span className="text-sm">Slip</span>
        {pins.length > 0 && (
          <span data-testid="bet-slip-count" className="min-w-5 h-5 px-1 rounded-full bg-zinc-950 text-emerald-400 text-xs font-bold flex items-center justify-center">{pins.length}</span>
        )}
      </button>

      <nav className="fixed bottom-0 inset-x-0 z-40 backdrop-blur-md bg-[#0A0D0E]/90 border-t border-zinc-800/80">
        <div className="max-w-5xl mx-auto grid grid-cols-5 h-16">
          {NAV.map(({ to, label, icon: Icon, testid }) => {
            const active = loc.pathname === to;
            return (
              <Link key={to} to={to} data-testid={testid}
                className={`flex flex-col items-center justify-center gap-0.5 text-[11px] font-medium transition-colors ${active ? "text-emerald-400" : "text-zinc-500 hover:text-zinc-300"}`}>
                <Icon className="w-5 h-5" />
                {label}
              </Link>
            );
          })}
        </div>
        <div className="bg-zinc-900 text-center py-1 px-3">
          <p className="text-[10px] text-zinc-500">18+ Gamble Responsibly — Chances are you're about to lose. Call 1800 858 858 · gamblinghelponline.org.au</p>
        </div>
      </nav>

      <BetSlipDrawer />
    </div>
  );
};
