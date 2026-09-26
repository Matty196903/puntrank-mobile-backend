import { useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { toast } from "sonner";
import api, { fmtErr } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

export default function ResetPasswordPage() {
  const [params] = useSearchParams();
  const token = params.get("token") || "";
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const nav = useNavigate();

  const submit = async (e) => {
    e.preventDefault();
    if (password !== confirm) { setError("Passwords do not match"); return; }
    setError(""); setBusy(true);
    try {
      await api.post("/auth/reset-password", { token, new_password: password });
      toast.success("Password updated — sign in with your new password");
      nav("/auth");
    } catch (err) {
      setError(fmtErr(err.response?.data?.detail) || err.message);
    } finally {
      setBusy(false);
    }
  };

  if (!token) {
    return (
      <div className="fade-up max-w-sm mx-auto py-12 text-center" data-testid="reset-password-page">
        <p className="text-sm text-zinc-400">This reset link is missing its token. Request a new one from the sign-in page.</p>
        <Link to="/auth" className="text-emerald-400 text-sm font-semibold hover:underline mt-3 inline-block">Back to sign in</Link>
      </div>
    );
  }

  return (
    <div className="fade-up max-w-sm mx-auto py-8" data-testid="reset-password-page">
      <h1 className="font-display text-4xl font-extrabold uppercase tracking-tight text-center">New Password</h1>
      <p className="text-sm text-zinc-400 text-center mt-1 mb-6">Choose a new password for your account.</p>
      <form onSubmit={submit} className="space-y-3">
        <Input data-testid="reset-password-input" type="password" required minLength={6} placeholder="New password (6+ characters)"
          value={password} onChange={(e) => setPassword(e.target.value)} className="bg-zinc-900 border-zinc-800 h-11" />
        <Input data-testid="reset-password-confirm" type="password" required minLength={6} placeholder="Confirm new password"
          value={confirm} onChange={(e) => setConfirm(e.target.value)} className="bg-zinc-900 border-zinc-800 h-11" />
        {error && <p className="text-sm text-red-400" data-testid="reset-password-error">{error}</p>}
        <Button data-testid="reset-password-submit" type="submit" disabled={busy}
          className="w-full h-11 rounded-full bg-emerald-600 hover:bg-emerald-500 text-white font-bold">
          {busy ? "Saving…" : "Set new password"}
        </Button>
      </form>
    </div>
  );
}
