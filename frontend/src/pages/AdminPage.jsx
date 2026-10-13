import { useCallback, useEffect, useState } from "react";
import { Shield, RefreshCw } from "lucide-react";
import { toast } from "sonner";
import api from "@/lib/api";
import { useAuth } from "@/context/AuthContext";
import { Button } from "@/components/ui/button";
import { Switch } from "@/components/ui/switch";

export default function AdminPage() {
  const { user } = useAuth();
  const [users, setUsers] = useState(null);
  const [pay, setPay] = useState(null);
  const [reseeding, setReseeding] = useState(false);

  const load = useCallback(() => {
    api.get("/admin/users").then((r) => setUsers(r.data.users)).catch(() => setUsers([]));
    api.get("/admin/payments").then((r) => setPay(r.data)).catch(() => setPay(null));
  }, []);
  useEffect(() => { if (user?.role === "admin") load(); }, [user, load]);

  if (user === undefined) return null;
  if (!user || user.role !== "admin") return <p className="text-sm text-zinc-400 py-10 text-center" data-testid="admin-denied">Admin access required.</p>;

  const reseed = async () => {
    setReseeding(true);
    try {
      await api.post("/admin/reseed");
      toast.success("Racing data reseeded for today (AEST)");
    } catch { toast.error("Reseed failed"); }
    setReseeding(false);
  };

  const togglePro = async (u) => {
    await api.post(`/admin/users/${u.id}/toggle-pro`);
    load();
    toast.success(`${u.email} — Pro ${u.is_pro ? "revoked" : "granted"}`);
  };

  return (
    <div className="fade-up" data-testid="admin-page">
      <div className="flex items-center gap-2">
        <Shield className="w-6 h-6 text-emerald-500" />
        <h1 className="font-display text-4xl font-extrabold uppercase tracking-tight">Admin</h1>
      </div>

      <div className="pr-card p-4 mt-4 flex items-center justify-between">
        <div>
          <p className="font-semibold text-sm">Reseed today's racing data</p>
          <p className="text-xs text-zinc-500">Regenerates meetings, races, runners and results for today (AEST).</p>
        </div>
        <Button data-testid="reseed-btn" onClick={reseed} disabled={reseeding} className="rounded-full bg-emerald-600 hover:bg-emerald-500">
          <RefreshCw className={`w-4 h-4 mr-2 ${reseeding ? "animate-spin" : ""}`} /> Reseed
        </Button>
      </div>

      {pay && (
        <>
          <h2 className="font-display text-2xl font-bold uppercase mt-6 mb-2">Payments (Stripe · {pay.mode} mode)</h2>
          <div className="grid grid-cols-2 gap-2 mb-3">
            <div className="pr-card p-3 text-center" data-testid="admin-revenue">
              <p className="font-mono-num text-xl font-bold text-emerald-400">A${pay.revenue.toFixed(2)}</p>
              <p className="text-[11px] text-zinc-500">Revenue ({pay.mode})</p>
            </div>
            <div className="pr-card p-3 text-center" data-testid="admin-paid-count">
              <p className="font-mono-num text-xl font-bold text-amber-400">{pay.paid_count}</p>
              <p className="text-[11px] text-zinc-500">Successful payments</p>
            </div>
          </div>
          <div className="space-y-2 max-h-72 overflow-y-auto pr-1" data-testid="admin-payments-list">
            {pay.transactions.length === 0 && <p className="text-xs text-zinc-500 py-3 text-center">No checkout attempts yet.</p>}
            {pay.transactions.map((t) => (
              <div key={t.session_id} className="pr-card p-3 flex items-center justify-between">
                <div className="min-w-0">
                  <p className="text-xs font-semibold truncate">{t.email || t.user_id}</p>
                  <p className="text-[11px] text-zinc-500">{t.lookup_key} · {new Date(t.created_at).toLocaleString("en-AU", { timeZone: "Australia/Sydney" })}</p>
                </div>
                <div className="text-right shrink-0 ml-2">
                  <p className="font-mono-num text-sm font-bold">A${(t.amount || 0).toFixed(2)}</p>
                  <span className={`text-[10px] font-bold px-1.5 py-0.5 rounded ${t.payment_status === "paid" ? "bg-emerald-500/20 text-emerald-400" : t.payment_status === "expired" ? "bg-red-500/20 text-red-400" : "bg-zinc-700/40 text-zinc-400"}`}>
                    {(t.payment_status || "pending").toUpperCase()}
                  </span>
                </div>
              </div>
            ))}
          </div>
          <p className="text-[11px] text-zinc-600 mt-2">Full detail (payouts, refunds, invoices) lives in your Stripe dashboard: dashboard.stripe.com</p>
        </>
      )}

      <h2 className="font-display text-2xl font-bold uppercase mt-6 mb-2">Users {users && `(${users.length})`}</h2>
      <div className="space-y-2">
        {users?.map((u) => (
          <div key={u.id} className="pr-card p-3.5 flex items-center justify-between" data-testid={`admin-user-${u.id}`}>
            <div>
              <p className="text-sm font-semibold">{u.email} {u.role === "admin" && <span className="text-[10px] font-bold text-amber-400 ml-1">ADMIN</span>}</p>
              <p className="text-xs text-zinc-500">{u.name || "—"} · Plan: {u.pro_plan || "free"}</p>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-xs text-zinc-500">Pro</span>
              <Switch data-testid={`toggle-pro-${u.id}`} checked={!!u.is_pro} onCheckedChange={() => togglePro(u)} disabled={u.role === "admin"} />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
