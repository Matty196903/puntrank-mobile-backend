export const fmtAest = (iso) =>
  new Date(iso).toLocaleTimeString("en-AU", {
    timeZone: "Australia/Sydney",
    hour: "numeric",
    minute: "2-digit",
    hour12: true,
  }).toUpperCase();
