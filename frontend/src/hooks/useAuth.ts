import { useState, useEffect, useCallback } from "react";
import { queryClient } from "../lib/queryClient";
import {
  signIn as cognitoSignIn,
  signUp as cognitoSignUp,
  confirmSignUp as cognitoConfirm,
  resendConfirmationCode as cognitoResendCode,
  signOut as cognitoSignOut,
  forgotPassword as cognitoForgotPassword,
  confirmForgotPassword as cognitoConfirmForgotPassword,
  changePassword as cognitoChangePassword,
  getSession,
} from "../lib/cognito";

interface AuthState {
  isAuthenticated: boolean;
  isLoading: boolean;
  email: string | null;
  error: string | null;
}

/**
 * useAuth — hook central de autenticacion.
 *
 * Expone todo el ciclo de auth de Cognito:
 * - signIn / signUp / confirmSignUp (registro + login)
 * - forgotPassword / confirmForgotPassword (recuperacion)
 * - changePassword (cambio desde perfil)
 * - signOut (cierre de sesion)
 *
 * Mantiene estado reactivo: isAuthenticated, isLoading, email, error.
 */
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
      queryClient.clear();
      setState({ isAuthenticated: true, isLoading: false, email: userEmail, error: null });
    } catch (err) {
      setState((s) => ({
        ...s,
        isLoading: false,
        error: err instanceof Error ? err.message : "Error de autenticacion",
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

  const resendVerificationCode = useCallback(async (email: string) => {
    await cognitoResendCode(email);
  }, []);

  const forgotPassword = useCallback(async (email: string) => {
    await cognitoForgotPassword(email);
  }, []);

  const confirmForgotPassword = useCallback(
    async (email: string, code: string, newPassword: string) => {
      await cognitoConfirmForgotPassword(email, code, newPassword);
    },
    [],
  );

  const changePassword = useCallback(
    async (oldPassword: string, newPassword: string) => {
      await cognitoChangePassword(oldPassword, newPassword);
    },
    [],
  );

  const signOut = useCallback(() => {
    cognitoSignOut();
    queryClient.clear();
    setState({ isAuthenticated: false, isLoading: false, email: null, error: null });
  }, []);

  return {
    ...state,
    signIn,
    signUp,
    confirmSignUp,
    resendVerificationCode,
    forgotPassword,
    confirmForgotPassword,
    changePassword,
    signOut,
  };
}
