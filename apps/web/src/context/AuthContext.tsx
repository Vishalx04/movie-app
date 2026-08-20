"use client";

import { authApi } from "@/lib/api/auth";
import { LoginPayload, SignupPayload, User } from "@/types/user";
import {
  createContext,
  ReactNode,
  useCallback,
  useContext,
  useEffect,
  useState,
} from "react";

interface AuthContextValue {
  user: User | null;
  access_token: string | null;
  isLoading: boolean;
  login: (payload: LoginPayload) => Promise<void>;
  signup: (payload: SignupPayload) => Promise<void>;
  logout : ()=> Promise<void>;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [access_token, setAccessToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const tryRestoreSession = useCallback(async () => {
    try {
      const tokenResponse = await authApi.refresh();
      const currentuser = await authApi.me(tokenResponse.access_token);
      setAccessToken(tokenResponse.access_token);
      setUser(currentuser);
    } catch {
      setAccessToken(null);
      setUser(null);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    tryRestoreSession();
  }, [tryRestoreSession]);

  const login = useCallback(async (payload: LoginPayload) => {
    const tokenResponse = await authApi.login(payload);
    const currentuser = await authApi.me(tokenResponse.access_token);
    setAccessToken(tokenResponse.access_token);
    setUser(currentuser);
  }, []);

  const signup = useCallback(
    async (payload: SignupPayload) => {
      await authApi.signup(payload);
      await login({ email: payload.email, password: payload.password });
    },
    [login],
  );

  const logout = useCallback(async () => {
    try {
      await authApi.logout();
    } catch {
    } finally {
      setAccessToken(null);
      setUser(null);
    }
  }, []);


  return (
    <AuthContext.Provider value = {{
        user, access_token, isLoading, login, signup, logout
    }} >
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth(): AuthContextValue{
  const context = useContext(AuthContext);
  if(context===undefined){
    throw new Error("useAuth must be used within an AuthProvider")
  }
  return context;
}
