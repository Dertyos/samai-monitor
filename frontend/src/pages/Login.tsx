import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";
import { useTheme } from "../hooks/useTheme";
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
    <div className={styles.page}>
      <button onClick={toggleTheme} className={`theme-toggle ${styles.themeToggle}`} title="Cambiar tema">
        {theme === "light" ? "\u{1F319}" : "\u{2600}\u{FE0F}"}
      </button>
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
  );
}
