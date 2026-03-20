import { useState, useEffect, useCallback } from "react";
import {
  signIn as cognitoSignIn,
  signUp as cognitoSignUp,
  confirmSignUp as cognitoConfirm,
  signOut as cognitoSignOut,
  getSession,
} from "../lib/cognito";

interface AuthState {
  isAuthenticated: boolean;
  isLoading: boolean;
  email: string | null;
  error: string | null;
}

export function useAuth() {
  const [state, setState] = useState<AuthState>({
    isAuthenticated: false,
    isLoading: true,
    email: null,
    error: null,
  });

  useEffect(() => {
    checkSession();
  }, []);

  const checkSession = async () => {
    try {
      const session = await getSession();
      const email = session.getIdToken().payload["email"] as string;
      setState({ isAuthenticated: true, isLoading: false, email, error: null });
    } catch {
      setState({ isAuthenticated: false, isLoading: false, email: null, error: null });
    }
  };

  const signIn = useCallback(async (email: string, password: string) => {
    setState((s) => ({ ...s, error: null, isLoading: true }));
    try {
      const session = await cognitoSignIn(email, password);
      const userEmail = session.getIdToken().payload["email"] as string;
      setState({ isAuthenticated: true, isLoading: false, email: userEmail, error: null });
    } catch (err) {
      setState((s) => ({
        ...s,
        isLoading: false,
        error: err instanceof Error ? err.message : "Error de autenticación",
      }));
      throw err;
    }
  }, []);

  const signUp = useCallback(async (email: string, password: string) => {
    await cognitoSignUp(email, password);
  }, []);

  const confirmSignUp = useCallback(async (email: string, code: string) => {
    await cognitoConfirm(email, code);
  }, []);

  const signOut = useCallback(() => {
    cognitoSignOut();
    setState({ isAuthenticated: false, isLoading: false, email: null, error: null });
  }, []);

  return { ...state, signIn, signUp, confirmSignUp, signOut };
}
