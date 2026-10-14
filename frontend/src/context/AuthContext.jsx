import { createContext, useContext, useEffect, useState, useCallback } from "react";
import api from "@/lib/api";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(undefined); // undefined=checking, null=anon/guest

  const refresh = useCallback(async () => {
    if (!localStorage.getItem("pr_token")) { setUser(null); return; }
    try {
      const { data } = await api.get("/auth/me");
      setUser(data);
    } catch {
      localStorage.removeItem("pr_token");
      setUser(null);
    }
  }, []);

  useEffect(() => { refresh(); }, [refresh]);

  const applyAuth = (data) => {
    localStorage.setItem("pr_token", data.access_token);
    localStorage.removeItem("pr_guest");
    setUser(data.user);
  };

  const login = async (email, password) => {
    const { data } = await api.post("/auth/login", { email, password });
    applyAuth(data);
  };

  const register = async (email, password, name) => {
    const { data } = await api.post("/auth/register", { email, password, name, origin_url: window.location.origin });
    applyAuth(data);
  };

  const logout = async () => {
    try { await api.post("/auth/logout"); } catch { /* ignore */ }
    localStorage.removeItem("pr_token");
    setUser(null);
  };

  const continueAsGuest = () => {
    localStorage.setItem("pr_guest", "1");
    setUser(null);
  };

  const isPro = !!(user && (user.is_pro || user.role === "admin"));

  return (
    <AuthContext.Provider value={{ user, isPro, login, register, logout, refresh, continueAsGuest }}>
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => useContext(AuthContext);
