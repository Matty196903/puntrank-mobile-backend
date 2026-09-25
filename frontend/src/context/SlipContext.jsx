import { createContext, useContext, useEffect, useState } from "react";
import { toast } from "sonner";

const SlipContext = createContext(null);

export function SlipProvider({ children }) {
  const [pins, setPins] = useState(() => {
    try { return JSON.parse(localStorage.getItem("pr_slip") || "[]"); } catch { return []; }
  });
  const [open, setOpen] = useState(false);

  useEffect(() => { localStorage.setItem("pr_slip", JSON.stringify(pins)); }, [pins]);

  const isPinned = (id) => pins.some((p) => p.id === id);

  const togglePin = (runner) => {
    setPins((prev) => {
      if (prev.some((p) => p.id === runner.id)) {
        toast("Removed from bet slip", { description: runner.name });
        return prev.filter((p) => p.id !== runner.id);
      }
      toast.success("Pinned to bet slip", { description: `${runner.number}. ${runner.name} @ $${runner.odds_current}` });
      return [...prev, runner];
    });
  };

  const clear = () => setPins([]);

  return (
    <SlipContext.Provider value={{ pins, togglePin, isPinned, clear, open, setOpen }}>
      {children}
    </SlipContext.Provider>
  );
}

export const useSlip = () => useContext(SlipContext);
