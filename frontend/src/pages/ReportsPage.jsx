import { useEffect, useState } from "react";
import { FileText, Download, Lock } from "lucide-react";
import { Link } from "react-router-dom";
import { toast } from "sonner";
import api from "@/lib/api";

export default function ReportsPage() {
  const [data, setData] = useState(null);
  const [busy, setBusy] = useState(null);
  useEffect(() => { api.get("/reports").then((r) => setData(r.data)); }, []);
  if (!data) return <p className="text-zinc-500 text-sm py-10 text-center">Loading reports…</p>;

  const download = async (key) => {
    setBusy(key);
    try {
      const res = await api.get(`/reports/${key}/download`, { responseType: "blob" });
      const url = URL.createObjectURL(res.data);
      const a = document.createElement("a");
      a.href = url;
      a.download = `puntrank_${key}.pdf`;
      a.click();
      URL.revokeObjectURL(url);
      toast.success("PDF downloaded");
    } catch {
      toast.error("Pro subscription required for this report");
    } finally {
      setBusy(null);
    }
  };

  return (
    <div className="fade-up" data-testid="reports-page">
      <div className="flex items-center gap-2">
        <FileText className="w-6 h-6 text-emerald-500" />
        <h1 className="font-display text-4xl font-extrabold uppercase tracking-tight">PDF Reports</h1>
      </div>
      <p className="text-sm text-zinc-400 mt-1 mb-4">Auto-generated guides, wraps and calculators — fresh for today's racing.</p>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
        {data.reports.map((r) => {
          const locked = r.pro && !data.pro;
          return (
            <div key={r.key} className="pr-card p-4 flex flex-col" data-testid={`report-card-${r.key}`}>
              <div className="flex items-center gap-2">
                <p className="font-display text-xl font-bold uppercase">{r.title}</p>
                {r.pro && <span className="text-[10px] font-bold px-1.5 py-0.5 rounded bg-amber-500/20 text-amber-400">PRO</span>}
              </div>
              <p className="text-xs text-zinc-500 mt-1 flex-1">{r.desc}</p>
              {locked ? (
                <Link to="/pricing" data-testid={`report-locked-${r.key}`}
                  className="mt-3 inline-flex items-center gap-1.5 text-xs font-semibold text-amber-400 hover:underline">
                  <Lock className="w-3.5 h-3.5" /> Unlock with Pro
                </Link>
              ) : (
                <button data-testid={`report-download-${r.key}`} onClick={() => download(r.key)} disabled={busy === r.key}
                  className="mt-3 inline-flex items-center gap-1.5 text-xs font-semibold px-3 py-2 rounded-full bg-emerald-600 hover:bg-emerald-500 text-white w-fit transition-colors disabled:opacity-50">
                  <Download className="w-3.5 h-3.5" /> {busy === r.key ? "Generating…" : "Download PDF"}
                </button>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
