import { Link } from "react-router-dom";
import { BookOpen, Trophy, Crown, TrendingDown, BarChart3, FileText, Ticket, ShieldAlert } from "lucide-react";

const GRADES = [
  { g: "A", style: "bg-emerald-500/15 text-emerald-400 border-emerald-500/30", title: "A-Grade — Strongest bets of the day", desc: "Rated a 28%+ winning chance with a confidence score of 84+. These are the model's most trusted runners — they appear on the A-Grade page and are graded live (WON / PLACED / UNPLACED) as results come in." },
  { g: "B", style: "bg-blue-500/15 text-blue-400 border-blue-500/30", title: "B-Grade — Solid win chances", desc: "Rated an 18%+ winning chance. Genuine winning hopes and each-way value — often the anchors for exotics and multis." },
  { g: "C", style: "bg-zinc-700/30 text-zinc-400 border-zinc-700", title: "C-Grade — Place hopes & exotics roughies", desc: "Longer-priced runners. Best used underneath in trifectas, first fours and quaddie legs rather than win bets." },
];

const SECTIONS = [
  { icon: Trophy, title: "Ace's Selections", desc: "Six decades of form craft in three lists: Winners (top-rated runners with a genuine winning chance), Places (runners rated 50%+ to run top-3), and the feature-meeting Quaddie (2 selections per leg across the last 4 races)." },
  { icon: Crown, title: "A-Grade Bets & Multis", desc: "Every A-Grade runner across all tracks, ranked by confidence, plus cross-race Doubles and Trebles built from the strongest upcoming picks. Graded live against official results." },
  { icon: TrendingDown, title: "Plunges / Market Movers", desc: "Runners whose PuntRank rated price is significantly shorter than their form-implied market price — where our model sees the biggest edge." },
  { icon: Ticket, title: "Bet Slip", desc: "Pin any runner to your slip, set a unit stake, and see total outlay and potential collect. It's a staking calculator only — PuntRank never takes bets." },
  { icon: BarChart3, title: "Results & Strike Rate", desc: "Every resulted race graded against Ace's top pick, with the daily win and place strike rates updated all day." },
  { icon: FileText, title: "PDF Reports", desc: "Downloadable form guide and Ace's Top 10 (free), plus Pro-only results wrap, A-Grade scorecard, staking calculator and printable Quaddie ticket." },
];

export default function GuidePage() {
  return (
    <div className="fade-up max-w-2xl mx-auto" data-testid="guide-page">
      <div className="flex items-center gap-2">
        <BookOpen className="w-6 h-6 text-emerald-500" />
        <h1 className="font-display text-4xl font-extrabold uppercase tracking-tight">How PuntRank Works</h1>
      </div>
      <p className="text-sm text-zinc-400 mt-2 leading-relaxed">
        PuntRank Aus ranks every runner at today's Australian TAB meetings using live Punting Form data —
        career win/place records, last-start form, distance and track records, barriers, weights and jockeys —
        run through Ace's 60-year selection system. Every runner gets a <span className="text-zinc-200 font-semibold">win probability</span>,
        a <span className="text-zinc-200 font-semibold">place probability</span>, a <span className="text-zinc-200 font-semibold">confidence score out of 100</span> and
        plain-English reasoning. It's a probability-ranking tool, not a betting service.
      </p>

      <h2 className="font-display text-2xl font-bold uppercase tracking-tight mt-7 mb-3">60-Second Video Tour</h2>
      <div className="pr-card p-2 overflow-hidden">
        <video data-testid="tutorial-video" controls playsInline preload="metadata"
          className="w-full max-w-[390px] mx-auto rounded-lg"
          src="/tutorial.mp4" />
        <p className="text-[11px] text-zinc-500 text-center py-2">Sign-up → reading the grades → Ace's quaddie → downloading PDFs</p>
      </div>

      <h2 className="font-display text-2xl font-bold uppercase tracking-tight mt-7 mb-3">The A / B / C Ratings</h2>
      <div className="space-y-2.5">
        {GRADES.map(({ g, style, title, desc }) => (
          <div key={g} className="pr-card p-4 flex gap-3" data-testid={`guide-grade-${g}`}>
            <span className={`shrink-0 w-9 h-9 rounded-lg border flex items-center justify-center font-display text-xl font-extrabold ${style}`}>{g}</span>
            <div>
              <p className="font-semibold text-sm">{title}</p>
              <p className="text-xs text-zinc-400 mt-1 leading-relaxed">{desc}</p>
            </div>
          </div>
        ))}
      </div>

      <h2 className="font-display text-2xl font-bold uppercase tracking-tight mt-7 mb-3">What's Inside</h2>
      <div className="space-y-2.5">
        {SECTIONS.map(({ icon: Icon, title, desc }) => (
          <div key={title} className="pr-card p-4 flex gap-3">
            <Icon className="w-5 h-5 text-emerald-400 shrink-0 mt-0.5" />
            <div>
              <p className="font-semibold text-sm">{title}</p>
              <p className="text-xs text-zinc-400 mt-1 leading-relaxed">{desc}</p>
            </div>
          </div>
        ))}
      </div>

      <h2 className="font-display text-2xl font-bold uppercase tracking-tight mt-7 mb-3">Free vs Pro</h2>
      <div className="pr-card p-4 text-sm text-zinc-300 leading-relaxed">
        <p><span className="font-semibold text-zinc-100">Free / guest:</span> today's meetings, full fields, top-3 reasoning per race, 2 Ace's winners, 1 A-Grade bet, 1 exotic per race, plunges, results, form guide + Ace's Top 10 PDFs.</p>
        <p className="mt-2"><span className="font-semibold text-amber-400">Pro (A$9.99/mo · A$49.99/yr · A$99 lifetime):</span> reasoning &amp; confidence for every runner, ALL A-Grade bets + multis, full exotics, Ace's complete Winners/Places/Quaddie, and every PDF including the Quaddie ticket and scorecard.</p>
        <Link to="/pricing" data-testid="guide-pricing-link" className="inline-block mt-3 px-4 py-2 rounded-full bg-amber-500 text-zinc-950 text-xs font-bold hover:bg-amber-400 transition-colors">See Pro plans</Link>
      </div>

      <div className="pr-card p-4 mt-5 border-amber-500/25 flex gap-3">
        <ShieldAlert className="w-5 h-5 text-amber-500 shrink-0 mt-0.5" />
        <p className="text-xs text-zinc-400 leading-relaxed">
          18+ only. PuntRank Aus is an informational probability-ranking tool — not a bookmaker, and no bets are placed here.
          Probabilities are estimates, not guarantees. Chances are you're about to lose. For free and confidential support call
          1800 858 858 or visit gamblinghelponline.org.au.
        </p>
      </div>
    </div>
  );
}
