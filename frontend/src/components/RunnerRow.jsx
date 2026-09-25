import { useState } from "react";
import { ChevronDown, Pin, Lock, ArrowDownRight } from "lucide-react";
import { Link } from "react-router-dom";
import { useSlip } from "@/context/SlipContext";

const GRADE_STYLE = {
  A: "bg-emerald-500/15 text-emerald-400 border-emerald-500/30",
  B: "bg-blue-500/15 text-blue-400 border-blue-500/30",
  C: "bg-zinc-700/30 text-zinc-400 border-zinc-700",
};

export const RunnerRow = ({ runner, track, raceNumber, result }) => {
  const [expanded, setExpanded] = useState(false);
  const { togglePin, isPinned } = useSlip();
  const pinned = isPinned(runner.id);
  const plunged = runner.odds_open > runner.odds_current;
  const winPos = result?.positions?.indexOf(runner.number);
  const finished = winPos != null && winPos >= 0 && winPos < 4 ? winPos + 1 : null;

  return (
    <div className={`pr-card ${runner.is_plunge ? "plunge-pulse border-red-500/40" : ""}`} data-testid={`runner-row-${runner.id}`}>
      <button onClick={() => setExpanded(!expanded)} className="w-full text-left p-3" data-testid={`runner-expand-${runner.id}`}>
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-lg bg-zinc-800 flex items-center justify-center font-display font-bold text-lg shrink-0">{runner.number}</div>
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2">
              <p className="font-semibold text-sm truncate">{runner.name}</p>
              {finished && <span className="text-[10px] font-bold px-1.5 py-0.5 rounded bg-amber-500/20 text-amber-400">{finished === 1 ? "WON" : `${finished}${["st","nd","rd","th"][finished-1]}`}</span>}
              <span className={`text-[10px] font-bold px-1.5 py-0.5 rounded border ${GRADE_STYLE[runner.grade]}`}>{runner.grade}</span>
            </div>
            <p className="text-xs text-zinc-500 truncate">Bar {runner.barrier} · {runner.jockey} · {runner.weight}kg · Form {runner.form}</p>
          </div>
          <div className="text-right shrink-0">
            <div className="flex items-center gap-1 justify-end">
              {plunged && <ArrowDownRight className="w-3.5 h-3.5 text-red-400" />}
              {plunged && <span className="font-mono-num text-[11px] text-zinc-500 line-through">${runner.odds_open}</span>}
              <span className="font-mono-num text-emerald-400 font-bold text-sm">${runner.odds_current}</span>
            </div>
            <p className="text-[11px] text-zinc-500">Win {(runner.win_prob * 100).toFixed(0)}% · Pl {(runner.place_prob * 100).toFixed(0)}%</p>
          </div>
          <ChevronDown className={`w-4 h-4 text-zinc-600 transition-transform ${expanded ? "rotate-180" : ""}`} />
        </div>
        <div className="prob-bar mt-2"><div style={{ width: `${Math.min(100, runner.win_prob * 220)}%` }} /></div>
      </button>
      {expanded && (
        <div className="px-3 pb-3 border-t border-zinc-800/70 pt-3 fade-up">
          {runner.reasoning ? (
            <>
              <div className="flex items-center gap-2 mb-2">
                <span className="text-[11px] font-bold text-zinc-400 uppercase tracking-wider">Confidence</span>
                <span className="font-mono-num text-sm text-amber-400 font-bold" data-testid={`runner-confidence-${runner.id}`}>{runner.confidence}/100</span>
              </div>
              <p className="text-sm text-zinc-300 leading-relaxed" data-testid={`runner-reasoning-${runner.id}`}>{runner.reasoning}</p>
            </>
          ) : (
            <div className="flex items-center gap-2 text-sm text-zinc-400" data-testid={`runner-locked-${runner.id}`}>
              <Lock className="w-4 h-4 text-amber-500" />
              <span>Full analysis &amp; confidence locked. <Link to="/pricing" className="text-amber-400 font-semibold hover:underline">Go Pro</Link> to unlock every runner.</span>
            </div>
          )}
          <button data-testid={`pin-runner-${runner.id}`}
            onClick={(e) => { e.stopPropagation(); togglePin({ ...runner, track, race_number: raceNumber }); }}
            className={`mt-3 flex items-center gap-1.5 text-xs font-semibold px-3 py-1.5 rounded-full border transition-colors ${pinned ? "bg-emerald-600 border-emerald-600 text-white" : "border-zinc-700 text-zinc-300 hover:border-emerald-500/60"}`}>
            <Pin className="w-3.5 h-3.5" /> {pinned ? "Pinned" : "Pin to slip"}
          </button>
        </div>
      )}
    </div>
  );
};
