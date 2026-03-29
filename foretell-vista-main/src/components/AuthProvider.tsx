import { createContext, useContext, useEffect, useState } from "react";
import { fetchAuthSession, logIn, logOut, signUp, type AuthUser } from "@/api/queries";
import { AUTH_EXPIRED_EVENT, ApiRequestError, getAuthToken, setAuthToken } from "@/api/client";

type AuthContextValue = {
  user: AuthUser | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  signup: (name: string, email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  refreshSession: () => Promise<void>;
};

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [loading, setLoading] = useState(true);

  const refreshSession = async () => {
    const token = getAuthToken();
    if (!token) {
      setUser(null);
      return;
    }
    const session = await fetchAuthSession();
    setUser(session.user);
  };

  useEffect(() => {
    const token = getAuthToken();
    if (!token) {
      setLoading(false);
      return;
    }
    refreshSession()
      .catch(() => {
        setAuthToken(null);
        setUser(null);
      })
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    const onExpired = () => setUser(null);
    window.addEventListener(AUTH_EXPIRED_EVENT, onExpired);
    return () => window.removeEventListener(AUTH_EXPIRED_EVENT, onExpired);
  }, []);

  const handleLogin = async (email: string, password: string) => {
    const session = await logIn(email, password);
    setAuthToken(session.token);
    setUser(session.user);
  };

  const handleSignup = async (name: string, email: string, password: string) => {
    const session = await signUp(name, email, password);
    setAuthToken(session.token);
    setUser(session.user);
  };

  const handleLogout = async () => {
    try {
      await logOut();
    } catch (error) {
      if (!(error instanceof ApiRequestError)) throw error;
    } finally {
      setAuthToken(null);
      setUser(null);
    }
  };

  return <AuthContext.Provider value={{ user, loading, login: handleLogin, signup: handleSignup, logout: handleLogout, refreshSession }}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) throw new Error("useAuth must be used within AuthProvider");
  return context;
}
