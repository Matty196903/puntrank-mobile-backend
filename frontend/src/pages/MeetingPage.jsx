import { useEffect, useState, useCallback } from "react";
import { useParams, Link } from "react-router-dom";
import { ArrowLeft, Copy } from "lucide-react";
import { toast } from "sonner";
import api from "@/lib/api";
import { RunnerRow } from "@/components/RunnerRow";
import { ProLock } from "@/components/ProLock";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { fmtAest } from "@/lib/time";

export default function MeetingPage() {
  const { id } = useParams();
  const [meta, setMeta] = useState(null);
  const [raceId, setRaceId] = useState(null);
  const [race, setRace] = useState(null);
  const [exotics, setExotics] = useState(null);

  useEffect(() => {
    api.get(`/meetings/${id}/races`).then((r) => {
      setMeta(r.data);
      const nxt = r.data.races.find((x) => x.status === "upcoming") || r.data.races[0];
      setRaceId(nxt.id);
    });
  }, [id]);

  const loadRace = useCallback((rid) => {
    setRace(null); setExotics(null);
    api.get(`/races/${rid}`).then((r) => setRace(r.data));
    api.get(`/races/${rid}/exotics`).then((r) => setExotics(r.data));
  }, []);

  useEffect(() => { if (raceId) loadRace(raceId); }, [raceId, loadRace]);

  if (!meta) return <p className="text-zinc-500 text-sm py-10 text-center">Loading race card…</p>;

  const copyExotic = (ex) => {
    navigator.clipboard?.writeText(`${ex.type}: ${ex.combo} (${ex.runners})`);
    toast.success("Copied", { description: ex.combo });
  };

  return (
    <div className="fade-up" data-testid="meeting-page">
      <Link to="/" data-testid="back-to-meetings" className="inline-flex items-center gap-1 text-sm text-zinc-400 hover:text-emerald-400 mb-3">
        <ArrowLeft className="w-4 h-4" /> Meetings
      </Link>
      <h1 className="font-display text-3xl font-extrabold uppercase tracking-tight">{meta.meeting.track}</h1>
      <p className="text-sm text-zinc-400">{meta.meeting.state} · {meta.meeting.condition} · Rail {meta.meeting.rail}</p>

      <div className="flex overflow-x-auto space-x-2 mt-4 pb-2 scrollbar-none">
        {meta.races.map((r) => (
          <button key={r.id} data-testid={`race-tab-${r.number}`} onClick={() => setRaceId(r.id)}
            className={`shrink-0 px-3.5 py-2 rounded-xl text-sm font-bold border transition-colors ${raceId === r.id ? "bg-emerald-600 border-emerald-600 text-white" : r.status === "resulted" ? "border-zinc-800 text-zinc-500" : "border-zinc-700 text-zinc-300 hover:border-emerald-500/60"}`}>
            R{r.number}
            <span className="block text-[10px] font-medium opacity-80">{r.status === "resulted" ? "Resulted" : fmtAest(r.start_aest)}</span>
          </button>
        ))}
      </div>

      {race && (
        <div className="mt-3">
          <div className="pr-card p-3 mb-4">
            <p className="font-semibold text-sm">Race {race.race.number} — {race.race.name}</p>
            <p className="text-xs text-zinc-500">{race.race.distance}m · {fmtAest(race.race.start_aest)} AEST {race.race.status === "resulted" && "· RESULTED"}</p>
            {race.race.result && (
              <p className="text-xs text-amber-400 mt-1 font-semibold" data-testid="race-result-line">
                Result: {race.race.result.positions.join(" - ")} · Win div ${race.race.result.win_dividend}
                {race.race.result.top_pick_won ? " · TOP PICK WON ✓" : race.race.result.top_pick_placed ? " · Top pick placed" : ""}
              </p>
            )}
          </div>

          <Tabs defaultValue="runners">
            <TabsList className="bg-zinc-900 border border-zinc-800">
              <TabsTrigger value="runners" data-testid="tab-runners">Runners</TabsTrigger>
              <TabsTrigger value="exotics" data-testid="tab-exotics">Exotics</TabsTrigger>
            </TabsList>
            <TabsContent value="runners" className="space-y-2.5 mt-3">
              {race.runners.map((r) => (
                <RunnerRow key={r.id} runner={r} track={meta.meeting.track} raceNumber={race.race.number} result={race.race.result} />
              ))}
            </TabsContent>
            <TabsContent value="exotics" className="space-y-2.5 mt-3">
              {exotics?.exotics.map((ex, i) => (
                <div key={i} className="pr-card p-4" data-testid={`exotic-card-${i}`}>
                  <div className="flex items-center justify-between">
                    <p className="font-display text-lg font-bold uppercase text-emerald-400">{ex.type}</p>
                    <button data-testid={`copy-exotic-${i}`} onClick={() => copyExotic(ex)} className="p-1.5 rounded-full hover:bg-zinc-800 text-zinc-400"><Copy className="w-4 h-4" /></button>
                  </div>
                  <p className="text-sm font-semibold mt-1">{ex.combo}</p>
                  <p className="text-xs text-zinc-500 mt-0.5">{ex.runners}</p>
                  <div className="flex gap-4 mt-2 text-xs">
                    <span className="text-zinc-400">Cost: <span className="font-mono-num text-zinc-200">A${ex.cost_per_unit.toFixed(2)}</span></span>
                    <span className="text-zinc-400">Est. return: <span className="font-mono-num text-amber-400">A${ex.est_return.toFixed(2)}</span></span>
                  </div>
                </div>
              ))}
              {exotics && exotics.locked > 0 && <ProLock count={exotics.locked} label="exotic combos" testid="exotics-pro-lock" />}
            </TabsContent>
          </Tabs>
        </div>
      )}
    </div>
  );
}
