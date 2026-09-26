import { useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { toast } from "sonner";
import api, { fmtErr } from "@/lib/api";
import { useAuth } from "@/context/AuthContext";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

export default function AuthPage() {
  const [mode, setMode] = useState("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [name, setName] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [sent, setSent] = useState(false);
  const { login, register, continueAsGuest } = useAuth();
  const nav = useNavigate();
  const [params] = useSearchParams();
  const next = params.get("next") || "/";

  const submit = async (e) => {
    e.preventDefault();
    setError(""); setBusy(true);
    try {
      if (mode === "forgot") {
        await api.post("/auth/forgot-password", { email, origin_url: window.location.origin });
        setSent(true);
      } else if (mode === "login") {
        await login(email, password);
        toast.success("Welcome back!");
        nav(next);
      } else {
        await register(email, password, name);
        toast.success("Account created");
        nav(next);
      }
    } catch (err) {
      setError(fmtErr(err.response?.data?.detail) || err.message);
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="fade-up max-w-sm mx-auto py-8" data-testid="auth-page">
      <h1 className="font-display text-4xl font-extrabold uppercase tracking-tight text-center">
        {mode === "login" ? "Sign In" : mode === "register" ? "Create Account" : "Reset Password"}
      </h1>
      <p className="text-sm text-zinc-400 text-center mt-1 mb-6">
        {mode === "forgot" ? "Enter your email and we'll send you a reset link." : "Your account syncs Pro status across web and the mobile app."}
      </p>

      {mode === "forgot" && sent ? (
        <div className="pr-card p-4 text-center" data-testid="forgot-sent-msg">
          <p className="text-sm text-emerald-400 font-semibold">Check your inbox</p>
          <p className="text-xs text-zinc-400 mt-1">If an account exists for {email}, a reset link is on its way. It expires in 1 hour.</p>
          <button data-testid="back-to-login-btn" onClick={() => { setMode("login"); setSent(false); }} className="text-sm text-emerald-400 hover:underline mt-3">Back to sign in</button>
        </div>
      ) : (
      <form onSubmit={submit} className="space-y-3">
        {mode === "register" && (
          <Input data-testid="auth-name-input" placeholder="Name (optional)" value={name} onChange={(e) => setName(e.target.value)}
            className="bg-zinc-900 border-zinc-800 h-11" />
        )}
        <Input data-testid="auth-email-input" type="email" required placeholder="Email" value={email} onChange={(e) => setEmail(e.target.value)}
          className="bg-zinc-900 border-zinc-800 h-11" />
        {mode !== "forgot" && (
        <Input data-testid="auth-password-input" type="password" required minLength={6} placeholder="Password (6+ characters)" value={password} onChange={(e) => setPassword(e.target.value)}
          className="bg-zinc-900 border-zinc-800 h-11" />
        )}
        {error && <p className="text-sm text-red-400" data-testid="auth-error">{error}</p>}
        <Button data-testid="auth-submit-btn" type="submit" disabled={busy}
          className="w-full h-11 rounded-full bg-emerald-600 hover:bg-emerald-500 text-white font-bold">
          {busy ? "Please wait…" : mode === "login" ? "Sign in" : mode === "register" ? "Create account" : "Send reset link"}
        </Button>
      </form>
      )}

      {mode === "login" && (
        <button data-testid="forgot-password-link" onClick={() => { setMode("forgot"); setError(""); }}
          className="w-full text-center text-sm text-zinc-400 mt-3 hover:text-emerald-400">
          Forgot your password?
        </button>
      )}
      {mode === "forgot" && !sent && (
        <button data-testid="back-to-login-link" onClick={() => { setMode("login"); setError(""); }}
          className="w-full text-center text-sm text-zinc-400 mt-3 hover:text-emerald-400">
          Back to sign in
        </button>
      )}

      <button data-testid="auth-switch-mode" onClick={() => { setMode(mode === "login" ? "register" : "login"); setError(""); }}
        className="w-full text-center text-sm text-zinc-400 mt-4 hover:text-emerald-400">
        {mode === "login" ? "No account? Create one free" : "Already have an account? Sign in"}
      </button>

      <div className="flex items-center gap-3 my-5">
        <div className="flex-1 h-px bg-zinc-800" /><span className="text-xs text-zinc-600">or</span><div className="flex-1 h-px bg-zinc-800" />
      </div>
      <Button data-testid="continue-guest-btn" variant="outline" onClick={() => { continueAsGuest(); nav("/"); }}
        className="w-full h-11 rounded-full border-zinc-700 bg-transparent text-zinc-300 hover:bg-zinc-900 hover:text-white">
        Continue as guest
      </Button>
      <p className="text-[11px] text-zinc-600 text-center mt-3">Guests can browse today's rankings. An account is needed for Pro.</p>
    </div>
  );
}
