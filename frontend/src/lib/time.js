import { useEffect, useState } from "react";

export function fmtAest(iso) {
  if (!iso) return "";
  return new Date(iso).toLocaleTimeString("en-AU", {
    hour: "numeric", minute: "2-digit", hour12: true, timeZone: "Australia/Sydney",
  });
}

export function useNow(intervalMs = 30000) {
  const [now, setNow] = useState(() => Date.now());
  useEffect(() => {
    const t = setInterval(() => setNow(Date.now()), intervalMs);
    return () => clearInterval(t);
  }, [intervalMs]);
  return now;
}

export function minsToJump(iso, now) {
  const diff = Math.round((new Date(iso).getTime() - now) / 60000);
  if (diff <= 0) return "JUMPING";
  if (diff < 60) return `${diff}m`;
  return `${Math.floor(diff / 60)}h ${diff % 60}m`;
}
