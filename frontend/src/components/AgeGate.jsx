import { useState } from "react";
import { ShieldAlert } from "lucide-react";
import { Button } from "@/components/ui/button";

export const AgeGate = ({ onConfirm }) => {
  const [declined, setDeclined] = useState(false);
  return (
    <div className="fixed inset-0 z-[100] bg-[#0A0D0E] flex items-center justify-center p-5" data-testid="age-gate-modal">
      <div className="max-w-sm w-full pr-card p-6 text-center fade-up">
        <div className="mx-auto w-14 h-14 rounded-full bg-amber-500/15 flex items-center justify-center mb-4">
          <ShieldAlert className="w-7 h-7 text-amber-500" />
        </div>
        <h1 className="font-display text-3xl font-extrabold uppercase tracking-tight">18+ Only</h1>
        <p className="text-sm text-zinc-400 mt-3 leading-relaxed">
          PuntRank Aus contains racing form analysis intended for adults. You must be 18 years or older to enter.
          This is a probability-ranking tool, not a betting service.
        </p>
        {declined ? (
          <p className="text-sm text-red-400 mt-4" data-testid="age-gate-declined-msg">
            You must be 18+ to use PuntRank Aus. If gambling is a problem for you or someone you know, call 1800 858 858.
          </p>
        ) : (
          <div className="mt-6 space-y-2">
            <Button data-testid="age-gate-confirm-btn" onClick={onConfirm}
              className="w-full bg-emerald-600 hover:bg-emerald-500 text-white font-semibold rounded-full h-11">
              I am 18 or older — Enter
            </Button>
            <Button data-testid="age-gate-decline-btn" variant="ghost" onClick={() => setDeclined(true)}
              className="w-full text-zinc-400 hover:text-zinc-200 rounded-full">
              I am under 18
            </Button>
          </div>
        )}
        <p className="text-[11px] text-zinc-600 mt-5">
          Chances are you're about to lose. For free and confidential support call 1800 858 858 or visit gamblinghelponline.org.au
        </p>
      </div>
    </div>
  );
};
