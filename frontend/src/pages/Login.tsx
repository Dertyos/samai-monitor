import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";
import { useTheme } from "../hooks/useTheme";
import styles from "./Login.module.css";

type Mode = "login" | "register" | "confirm";

/**
 * Login — pagina publica de autenticacion.
 *
 * Maneja 3 modos: login, register, confirm (codigo de verificacion).
 * Al autenticarse exitosamente, redirige a /dashboard.
 * Usa Cognito como proveedor de identidad.
 */
export default function Login() {
  const navigate = useNavigate();
  const auth = useAuth();
  const { theme, toggle: toggleTheme } = useTheme();
  const [mode, setMode] = useState<Mode>("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [code, setCode] = useState("");
  const [loading, setLoading] = useState(false);
  const [localError, setLocalError] = useState<string | null>(null);

  const err = localError || auth.error;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setLocalError(null);
    try {
      if (mode === "login") {
        await auth.signIn(email, password);
        navigate("/dashboard", { replace: true });
      } else if (mode === "register") {
        await auth.signUp(email, password);
        setMode("confirm");
      } else {
        await auth.confirmSignUp(email, code);
        await auth.signIn(email, password);
        navigate("/dashboard", { replace: true });
      }
    } catch (err) {
      setLocalError(err instanceof Error ? err.message : "Error");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className={styles.page}>
      <button onClick={toggleTheme} className={`theme-toggle ${styles.themeToggle}`} title="Cambiar tema">
        {theme === "light" ? "\u{1F319}" : "\u{2600}\u{FE0F}"}
      </button>
      <div className={styles.card}>
        <h1>SAMAI Monitor</h1>
        <p className={styles.subtitle}>Monitoreo de estados judiciales</p>

        <div className={styles.tabs}>
          <button
            className={mode === "login" ? "active" : ""}
            onClick={() => setMode("login")}
          >
            Iniciar Sesion
          </button>
          <button
            className={mode === "register" || mode === "confirm" ? "active" : ""}
            onClick={() => setMode("register")}
          >
            Registrarse
          </button>
        </div>

        <form onSubmit={handleSubmit}>
          <input
            type="email"
            placeholder="Correo electronico"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />
          {mode !== "confirm" && (
            <input
              type="password"
              placeholder="Contrasena"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              minLength={8}
            />
          )}
          {mode === "confirm" && (
            <input
              type="text"
              placeholder="Codigo de verificacion"
              value={code}
              onChange={(e) => setCode(e.target.value)}
              required
            />
          )}
          {err && <div className="error">{err}</div>}
          <button type="submit" className="primary" disabled={loading}>
            {loading
              ? "..."
              : mode === "login"
                ? "Iniciar Sesion"
                : mode === "register"
                  ? "Registrarse"
                  : "Confirmar"}
          </button>
        </form>
      </div>
    </div>
  );
}
