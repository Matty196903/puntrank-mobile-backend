import { useEffect, useRef, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { CheckCircle2, Loader2, XCircle } from "lucide-react";
import api from "@/lib/api";
import { useAuth } from "@/context/AuthContext";

export default function PaymentSuccessPage() {
  const [params] = useSearchParams();
  const sessionId = params.get("session_id");
  const [state, setState] = useState("checking");
  const { refresh } = useAuth();
  const tries = useRef(0);

  useEffect(() => {
    if (!sessionId) { setState("error"); return; }
    let stop = false;
    const poll = async () => {
      if (stop || tries.current > 10) { if (tries.current > 10) setState("timeout"); return; }
      tries.current += 1;
      try {
        const { data } = await api.get(`/payments/status/${sessionId}`);
        if (data.payment_status === "paid") { setState("paid"); refresh(); return; }
        if (["expired", "failed"].includes(data.payment_status)) { setState("error"); return; }
      } catch { /* keep polling */ }
      setTimeout(poll, 2000);
    };
    poll();
    return () => { stop = true; };
  }, [sessionId, refresh]);

  return (
    <div className="fade-up max-w-sm mx-auto text-center py-16" data-testid="payment-success-page">
      {state === "checking" && (
        <>
          <Loader2 className="w-10 h-10 text-emerald-500 mx-auto animate-spin" />
          <h1 className="font-display text-3xl font-extrabold uppercase mt-4">Confirming payment…</h1>
          <p className="text-sm text-zinc-400 mt-2">Hang tight — verifying with Stripe.</p>
        </>
      )}
      {state === "paid" && (
        <>
          <CheckCircle2 className="w-12 h-12 text-emerald-500 mx-auto" />
          <h1 className="font-display text-3xl font-extrabold uppercase mt-4" data-testid="payment-confirmed">You're Pro!</h1>
          <p className="text-sm text-zinc-400 mt-2">Payment confirmed. Every A-Grade bet, exotic and report is now unlocked — on web and in the mobile app.</p>
          <Link to="/best-bets" data-testid="goto-best-bets" className="inline-block mt-5 px-5 py-2.5 rounded-full bg-emerald-600 hover:bg-emerald-500 text-white text-sm font-bold">See today's A-Grade bets</Link>
        </>
      )}
      {(state === "error" || state === "timeout") && (
        <>
          <XCircle className="w-12 h-12 text-red-500 mx-auto" />
          <h1 className="font-display text-3xl font-extrabold uppercase mt-4">{state === "timeout" ? "Still processing" : "Payment issue"}</h1>
          <p className="text-sm text-zinc-400 mt-2">{state === "timeout" ? "Your payment is still processing. Pro will unlock automatically once confirmed." : "We couldn't confirm this payment. You have not been charged if the checkout was cancelled."}</p>
          <Link to="/pricing" className="inline-block mt-5 px-5 py-2.5 rounded-full border border-zinc-700 text-sm font-semibold hover:border-emerald-500/60">Back to pricing</Link>
        </>
      )}
    </div>
  );
}
