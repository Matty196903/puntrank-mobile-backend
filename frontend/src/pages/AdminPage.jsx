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
  const [reseeding, setReseeding] = useState(false);

  const load = useCallback(() => { api.get("/admin/users").then((r) => setUsers(r.data.users)).catch(() => setUsers([])); }, []);
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
