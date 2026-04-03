import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";
import { useTheme } from "../hooks/useTheme";
import { getGoogleLoginUrl } from "../lib/cognito";
import { DotLottieReact } from '@lottiefiles/dotlottie-react';
import styles from "./Login.module.css";

/**
 * Modos de la pagina de login:
 * - login: iniciar sesion con email + password
 * - register: crear cuenta nueva
 * - verifyEmail: ingresar codigo de verificacion enviado al correo tras registro
 * - forgot: solicitar codigo de recuperacion de contrasena
 * - resetPassword: ingresar codigo + nueva contrasena
 */
type Mode = "login" | "register" | "verifyEmail" | "forgot" | "resetPassword";

/**
 * Login — pagina publica de autenticacion.
 *
 * Maneja todo el ciclo de auth: login, registro, confirmacion,
 * forgot password y reset password. Redirige a /dashboard al autenticarse.
 */
export default function Login() {
  const navigate = useNavigate();
  const auth = useAuth();
  const { theme, toggle: toggleTheme } = useTheme();
  const [mode, setMode] = useState<Mode>("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [code, setCode] = useState("");
  const [loading, setLoading] = useState(false);
  const [localError, setLocalError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  const err = localError || auth.error;

  const clearMessages = () => {
    setLocalError(null);
    setSuccessMsg(null);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    clearMessages();
    try {
      switch (mode) {
        case "login":
          await auth.signIn(email, password);
          navigate("/dashboard", { replace: true });
          break;

        case "register":
          await auth.signUp(email, password);
          setMode("verifyEmail");
          setSuccessMsg("Codigo enviado a tu correo. Ingrésalo para activar tu cuenta.");
          break;

        case "verifyEmail":
          await auth.confirmSignUp(email, code);
          await auth.signIn(email, password);
          navigate("/dashboard", { replace: true });
          break;

        case "forgot":
          await auth.forgotPassword(email);
          setMode("resetPassword");
          setSuccessMsg("Codigo de recuperacion enviado a tu correo");
          break;

        case "resetPassword":
          await auth.confirmForgotPassword(email, code, newPassword);
          setSuccessMsg("Contrasena actualizada. Inicia sesion.");
          setMode("login");
          setPassword("");
          setCode("");
          setNewPassword("");
          break;
      }
    } catch (err) {
      setLocalError(err instanceof Error ? err.message : "Error");
    } finally {
      setLoading(false);
    }
  };

  const switchToForgot = () => {
    clearMessages();
    setMode("forgot");
  };

  const switchToLogin = () => {
    clearMessages();
    setMode("login");
  };

  const getSubmitLabel = (): string => {
    if (loading) return "...";
    switch (mode) {
      case "login": return "Iniciar Sesion";
      case "register": return "Registrarse";
      case "verifyEmail": return "Verificar cuenta";
      case "forgot": return "Enviar codigo";
      case "resetPassword": return "Cambiar contrasena";
    }
  };

  const showTabs = mode === "login" || mode === "register";
  const showBackToLogin = mode === "forgot" || mode === "resetPassword" || mode === "verifyEmail";

  return (
    <div className={styles.splitLayout}>
      <button onClick={toggleTheme} className={`theme-toggle ${styles.themeToggle}`} title="Cambiar tema">
        {theme === "light" ? "\u{1F319}" : "\u{2600}\u{FE0F}"}
      </button>

      {/* Seccion Izquierda: Animacion visual (oculta en moviles) */}
      <div className={styles.visualSection}>
        <div className={styles.lottieWrapper}>
          <DotLottieReact
            src="https://lottie.host/362a69c0-207b-4efe-8411-6a0f4acc6a71/ZYcOWiINyi.lottie"
            loop
            autoplay
          />
        </div>
      </div>

      {/* Seccion Derecha: Formulario de Login/Registro */}
      <div className={styles.formSection}>
        <div className={styles.card}>
        <h1>Alertas Judiciales<br /><small>by Dertyos</small></h1>
        <p className={styles.subtitle}>Monitoreo de estados judiciales</p>

        {showTabs && (
          <div className={styles.tabs}>
            <button
              className={mode === "login" ? "active" : ""}
              onClick={() => { clearMessages(); setMode("login"); }}
            >
              Iniciar Sesion
            </button>
            <button
              className={mode === "register" ? "active" : ""}
              onClick={() => { clearMessages(); setMode("register"); }}
            >
              Registrarse
            </button>
          </div>
        )}

        {showBackToLogin && (
          <div style={{ marginBottom: "1rem" }}>
            <button className={styles.forgotLink} onClick={switchToLogin}>
              &larr; Volver a iniciar sesion
            </button>
            <h3 style={{ marginTop: "0.5rem" }}>
              {mode === "verifyEmail" && "Verifica tu correo"}
              {mode === "forgot" && "Recuperar contrasena"}
              {mode === "resetPassword" && "Nueva contrasena"}
            </h3>
          </div>
        )}

        <form onSubmit={handleSubmit}>
          {/* Email — siempre visible */}
          <label>
            Correo electronico
            <input
              type="email"
              placeholder="nombre@ejemplo.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              autoComplete="email"
            />
          </label>

          {/* Password — login y register */}
          {(mode === "login" || mode === "register") && (
            <label>
              Contrasena
              <input
                type="password"
                placeholder="Minimo 8 caracteres"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                minLength={8}
                autoComplete={mode === "login" ? "current-password" : "new-password"}
              />
            </label>
          )}

          {/* Link forgot password — solo en login */}
          {mode === "login" && (
            <button type="button" className={styles.forgotLink} onClick={switchToForgot}>
              Olvidaste tu contrasena?
            </button>
          )}

          {/* Codigo verificacion — verifyEmail y resetPassword */}
          {(mode === "verifyEmail" || mode === "resetPassword") && (
            <label>
              Codigo de verificacion
              <input
                type="text"
                placeholder="Codigo de verificacion (6 digitos)"
                value={code}
                onChange={(e) => setCode(e.target.value)}
                required
                maxLength={6}
                inputMode="numeric"
                autoComplete="one-time-code"
              />
            </label>
          )}

          {/* Nueva contrasena — resetPassword */}
          {mode === "resetPassword" && (
            <label>
              Nueva contrasena
              <input
                type="password"
                placeholder="Minimo 8 caracteres"
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                required
                minLength={8}
                autoComplete="new-password"
              />
            </label>
          )}

          {successMsg && <div className="success-msg">{successMsg}</div>}
          {err && <div className="error">{err}</div>}

          <button type="submit" className="primary" disabled={loading}>
            {getSubmitLabel()}
          </button>

          {(mode === "login" || mode === "register") && (
            <>
              <div className={styles.divider}>
                <span>o</span>
              </div>
              <a href={getGoogleLoginUrl()} className={styles.googleBtn}>
                <svg width="18" height="18" viewBox="0 0 48 48">
                  <path fill="#EA4335" d="M24 9.5c3.54 0 6.71 1.22 9.21 3.6l6.85-6.85C35.9 2.38 30.47 0 24 0 14.62 0 6.51 5.38 2.56 13.22l7.98 6.19C12.43 13.72 17.74 9.5 24 9.5z"/>
                  <path fill="#4285F4" d="M46.98 24.55c0-1.57-.15-3.09-.38-4.55H24v9.02h12.94c-.58 2.96-2.26 5.48-4.78 7.18l7.73 6c4.51-4.18 7.09-10.36 7.09-17.65z"/>
                  <path fill="#FBBC05" d="M10.53 28.59a14.5 14.5 0 0 1 0-9.18l-7.98-6.19a24.0 24.0 0 0 0 0 21.56l7.98-6.19z"/>
                  <path fill="#34A853" d="M24 48c6.48 0 11.93-2.13 15.89-5.81l-7.73-6c-2.15 1.45-4.92 2.3-8.16 2.3-6.26 0-11.57-4.22-13.47-9.91l-7.98 6.19C6.51 42.62 14.62 48 24 48z"/>
                </svg>
                Continuar con Google
              </a>
            </>
          )}

          {mode === "verifyEmail" && (
            <button
              type="button"
              className={styles.forgotLink}
              disabled={loading}
              onClick={async () => {
                clearMessages();
                try {
                  await auth.resendVerificationCode(email);
                  setSuccessMsg("Codigo reenviado. Revisa tu correo.");
                } catch (e) {
                  setLocalError(e instanceof Error ? e.message : "Error al reenviar");
                }
              }}
            >
              Reenviar codigo
            </button>
          )}
        </form>
        </div>
      </div>
    </div>
  );
}
