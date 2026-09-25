import { useState } from "react";
import { Sheet, SheetContent, SheetHeader, SheetTitle } from "@/components/ui/sheet";
import { Button } from "@/components/ui/button";
import { Trash2, X } from "lucide-react";
import { useSlip } from "@/context/SlipContext";

export const BetSlipDrawer = () => {
  const { pins, togglePin, clear, open, setOpen } = useSlip();
  const [unit, setUnit] = useState(10);

  const totalStake = pins.length * unit;
  const potential = pins.reduce((acc, p) => acc + unit * p.odds_current, 0);

  return (
    <Sheet open={open} onOpenChange={setOpen}>
      <SheetContent side="right" className="bg-[#0F1416] border-zinc-800 text-zinc-100 w-full sm:max-w-md overflow-y-auto" data-testid="bet-slip-drawer">
        <SheetHeader>
          <SheetTitle className="font-display text-2xl uppercase text-zinc-100">Bet Slip</SheetTitle>
        </SheetHeader>
        <p className="text-xs text-zinc-500 mb-4">Simulation only — PuntRank does not take bets. Unit staking calculator for your pinned runners.</p>
        {pins.length === 0 ? (
          <p className="text-sm text-zinc-400 py-8 text-center" data-testid="bet-slip-empty">No runners pinned yet. Tap the pin icon on any runner to add it here.</p>
        ) : (
          <>
            <div className="space-y-2">
              {pins.map((p) => (
                <div key={p.id} className="pr-card p-3 flex items-center justify-between" data-testid={`slip-item-${p.id}`}>
                  <div>
                    <p className="text-sm font-semibold">{p.number}. {p.name}</p>
                    <p className="text-xs text-zinc-500">{p.track} R{p.race_number} · Win {(p.win_prob * 100).toFixed(0)}% · Grade {p.grade}</p>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="font-mono-num text-emerald-400 text-sm">${p.odds_current}</span>
                    <button data-testid={`slip-remove-${p.id}`} onClick={() => togglePin(p)} className="p-1.5 rounded-full hover:bg-zinc-800 text-zinc-500">
                      <X className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              ))}
            </div>
            <div className="mt-5 pr-card p-4">
              <label className="text-xs text-zinc-400 font-medium">Unit stake (A$)</label>
              <input data-testid="unit-stake-input" type="number" min="1" value={unit}
                onChange={(e) => setUnit(Math.max(1, Number(e.target.value) || 1))}
                className="mt-1 w-full bg-zinc-900 border border-zinc-800 rounded-lg px-3 py-2 text-sm font-mono-num focus:outline-none focus:border-emerald-500/60" />
              <div className="mt-3 space-y-1 text-sm">
                <div className="flex justify-between text-zinc-400"><span>Total outlay</span><span className="font-mono-num text-zinc-200">A${totalStake.toFixed(2)}</span></div>
                <div className="flex justify-between text-zinc-400"><span>Potential collect (all win)</span><span className="font-mono-num text-emerald-400" data-testid="potential-return">A${potential.toFixed(2)}</span></div>
              </div>
            </div>
            <Button data-testid="clear-slip-btn" variant="ghost" onClick={clear} className="mt-4 w-full text-red-400 hover:text-red-300 hover:bg-red-950/30">
              <Trash2 className="w-4 h-4 mr-2" /> Clear slip
            </Button>
          </>
        )}
      </SheetContent>
    </Sheet>
  );
};
