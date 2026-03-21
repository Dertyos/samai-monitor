import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";
import { useTheme } from "../hooks/useTheme";
import styles from "./Login.module.css";

/**
 * Modos de la pagina de login:
 * - login: iniciar sesion con email + password
 * - register: crear cuenta nueva
 * - confirm: verificar codigo de email (post-registro)
 * - forgot: solicitar codigo de recuperacion de contrasena
 * - resetPassword: ingresar codigo + nueva contrasena
 */
type Mode = "login" | "register" | "confirm" | "forgot" | "resetPassword";

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
          setMode("confirm");
          setSuccessMsg("Codigo de verificacion enviado a tu correo");
          break;

        case "confirm":
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
      case "confirm": return "Confirmar";
      case "forgot": return "Enviar codigo";
      case "resetPassword": return "Cambiar contrasena";
    }
  };

  const showTabs = mode === "login" || mode === "register" || mode === "confirm";

  return (
    <div className={styles.page}>
      <button onClick={toggleTheme} className={`theme-toggle ${styles.themeToggle}`} title="Cambiar tema">
        {theme === "light" ? "\u{1F319}" : "\u{2600}\u{FE0F}"}
      </button>
      <div className={styles.card}>
        <h1>SAMAI Monitor</h1>
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
              className={mode === "register" || mode === "confirm" ? "active" : ""}
              onClick={() => { clearMessages(); setMode("register"); }}
            >
              Registrarse
            </button>
          </div>
        )}

        {(mode === "forgot" || mode === "resetPassword") && (
          <div style={{ marginBottom: "1rem" }}>
            <button className={styles.forgotLink} onClick={switchToLogin}>
              &larr; Volver a iniciar sesion
            </button>
            <h3 style={{ marginTop: "0.5rem" }}>
              {mode === "forgot" ? "Recuperar contrasena" : "Nueva contrasena"}
            </h3>
          </div>
        )}

        <form onSubmit={handleSubmit}>
          {/* Email — siempre visible */}
          <input
            type="email"
            placeholder="Correo electronico"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />

          {/* Password — login y register */}
          {(mode === "login" || mode === "register") && (
            <input
              type="password"
              placeholder="Contrasena"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              minLength={8}
            />
          )}

          {/* Link forgot password — solo en login */}
          {mode === "login" && (
            <button type="button" className={styles.forgotLink} onClick={switchToForgot}>
              Olvidaste tu contrasena?
            </button>
          )}

          {/* Codigo verificacion — confirm y resetPassword */}
          {(mode === "confirm" || mode === "resetPassword") && (
            <input
              type="text"
              placeholder="Codigo de verificacion"
              value={code}
              onChange={(e) => setCode(e.target.value)}
              required
            />
          )}

          {/* Nueva contrasena — resetPassword */}
          {mode === "resetPassword" && (
            <input
              type="password"
              placeholder="Nueva contrasena"
              value={newPassword}
              onChange={(e) => setNewPassword(e.target.value)}
              required
              minLength={8}
            />
          )}

          {successMsg && <div className="success-msg">{successMsg}</div>}
          {err && <div className="error">{err}</div>}

          <button type="submit" className="primary" disabled={loading}>
            {getSubmitLabel()}
          </button>
        </form>
      </div>
    </div>
  );
}
