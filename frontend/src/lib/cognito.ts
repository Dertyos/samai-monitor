import {
  CognitoUserPool,
  CognitoUser,
  AuthenticationDetails,
  CognitoUserSession,
  CognitoUserAttribute,
  CognitoIdToken,
  CognitoAccessToken,
  CognitoRefreshToken,
} from "amazon-cognito-identity-js";
import { COGNITO_CONFIG } from "../config/auth";

const userPool = new CognitoUserPool({
  UserPoolId: COGNITO_CONFIG.userPoolId,
  ClientId: COGNITO_CONFIG.userPoolClientId,
});

export function getCurrentUser(): CognitoUser | null {
  return userPool.getCurrentUser();
}

export function getSession(): Promise<CognitoUserSession> {
  return new Promise((resolve, reject) => {
    const user = getCurrentUser();
    if (!user) {
      reject(new Error("No user"));
      return;
    }
    user.getSession(
      (err: Error | null, session: CognitoUserSession | null) => {
        if (err || !session) {
          reject(err || new Error("No session"));
          return;
        }
        resolve(session);
      }
    );
  });
}

export function getIdToken(): Promise<string> {
  return getSession().then((s) => s.getIdToken().getJwtToken());
}

export function signIn(email: string, password: string): Promise<CognitoUserSession> {
  return new Promise((resolve, reject) => {
    const user = new CognitoUser({ Username: email, Pool: userPool });
    const authDetails = new AuthenticationDetails({
      Username: email,
      Password: password,
    });
    user.authenticateUser(authDetails, {
      onSuccess: resolve,
      onFailure: reject,
      newPasswordRequired: () => {
        reject(new Error("NEW_PASSWORD_REQUIRED"));
      },
    });
  });
}

export function signUp(email: string, password: string): Promise<void> {
  return new Promise((resolve, reject) => {
    const attrs = [
      new CognitoUserAttribute({ Name: "email", Value: email }),
    ];
    userPool.signUp(email, password, attrs, [], (err) => {
      if (err) {
        reject(err);
        return;
      }
      resolve();
    });
  });
}

export function confirmSignUp(email: string, code: string): Promise<void> {
  return new Promise((resolve, reject) => {
    const user = new CognitoUser({ Username: email, Pool: userPool });
    user.confirmRegistration(code, true, (err) => {
      if (err) {
        reject(err);
        return;
      }
      resolve();
    });
  });
}

export function resendConfirmationCode(email: string): Promise<void> {
  return new Promise((resolve, reject) => {
    const user = new CognitoUser({ Username: email, Pool: userPool });
    user.resendConfirmationCode((err) => {
      if (err) {
        reject(err);
        return;
      }
      resolve();
    });
  });
}

export function signOut(): void {
  const user = getCurrentUser();
  if (user) {
    user.signOut();
  }
}

/**
 * forgotPassword — inicia el flujo de recuperacion de contrasena.
 *
 * Envia un codigo de verificacion al email registrado en Cognito.
 * Despues de esto, el usuario debe llamar confirmForgotPassword con el codigo.
 */
export function forgotPassword(email: string): Promise<void> {
  return new Promise((resolve, reject) => {
    const user = new CognitoUser({ Username: email, Pool: userPool });
    user.forgotPassword({
      onSuccess: () => resolve(),
      onFailure: reject,
      inputVerificationCode: () => resolve(),
    });
  });
}

/**
 * confirmForgotPassword — completa el flujo de recuperacion.
 *
 * Recibe el codigo de verificacion enviado por email y la nueva contrasena.
 * Valida el codigo contra Cognito y actualiza la contrasena.
 */
export function confirmForgotPassword(
  email: string,
  code: string,
  newPassword: string,
): Promise<void> {
  return new Promise((resolve, reject) => {
    const user = new CognitoUser({ Username: email, Pool: userPool });
    user.confirmPassword(code, newPassword, {
      onSuccess: () => resolve(),
      onFailure: reject,
    });
  });
}

/**
 * changePassword — cambia la contrasena del usuario autenticado.
 *
 * Requiere sesion activa. Usado desde la pagina de perfil.
 */
export function changePassword(
  oldPassword: string,
  newPassword: string,
): Promise<void> {
  return new Promise((resolve, reject) => {
    const user = getCurrentUser();
    if (!user) {
      reject(new Error("No authenticated user"));
      return;
    }
    user.getSession((err: Error | null) => {
      if (err) {
        reject(err);
        return;
      }
      user.changePassword(oldPassword, newPassword, (err) => {
        if (err) {
          reject(err);
          return;
        }
        resolve();
      });
    });
  });
}

export function getGoogleLoginUrl(): string {
  const callbackUrl = `${window.location.origin}/callback`;
  const params = new URLSearchParams({
    identity_provider: "Google",
    redirect_uri: callbackUrl,
    response_type: "token",
    client_id: COGNITO_CONFIG.userPoolClientId,
    scope: "email openid profile",
  });
  return `https://${COGNITO_CONFIG.domain}/oauth2/authorize?${params}`;
}

export function handleOAuthCallback(hash: string): CognitoUserSession {
  const params = new URLSearchParams(hash.replace("#", "?"));
  const idTokenStr = params.get("id_token");
  const accessTokenStr = params.get("access_token");

  if (!idTokenStr || !accessTokenStr) {
    throw new Error("Tokens no encontrados en la URL");
  }

  const idToken = new CognitoIdToken({ IdToken: idTokenStr });
  const accessToken = new CognitoAccessToken({ AccessToken: accessTokenStr });
  const refreshToken = new CognitoRefreshToken({ RefreshToken: "" });

  const session = new CognitoUserSession({
    IdToken: idToken,
    AccessToken: accessToken,
    RefreshToken: refreshToken,
  });

  const username = idToken.payload["cognito:username"] as string || idToken.payload["sub"] as string;
  const user = new CognitoUser({ Username: username, Pool: userPool });
  user.setSignInUserSession(session);

  return session;
}
