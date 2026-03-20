import { useState } from "react";
import { useTheme } from "../hooks/useTheme";

interface Props {
  onSignIn: (email: string, password: string) => Promise<void>;
  onSignUp: (email: string, password: string) => Promise<void>;
  onConfirm: (email: string, code: string) => Promise<void>;
  error: string | null;
}

type Mode = "login" | "register" | "confirm";

export default function Login({ onSignIn, onSignUp, onConfirm, error }: Props) {
  const { theme, toggle: toggleTheme } = useTheme();
  const [mode, setMode] = useState<Mode>("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [code, setCode] = useState("");
  const [loading, setLoading] = useState(false);
  const [localError, setLocalError] = useState<string | null>(null);

  const err = localError || error;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setLocalError(null);
    try {
      if (mode === "login") {
        await onSignIn(email, password);
      } else if (mode === "register") {
        await onSignUp(email, password);
        setMode("confirm");
      } else {
        await onConfirm(email, code);
        await onSignIn(email, password);
      }
    } catch (err) {
      setLocalError(err instanceof Error ? err.message : "Error");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-page">
      <button onClick={toggleTheme} className="theme-toggle login-theme-toggle" title="Cambiar tema">
        {theme === "light" ? "\u{1F319}" : "\u{2600}\u{FE0F}"}
      </button>
      <div className="login-card">
        <h1>SAMAI Monitor</h1>
        <p className="subtitle">Monitoreo de estados judiciales</p>

        <div className="tabs">
          <button
            className={mode === "login" ? "active" : ""}
            onClick={() => setMode("login")}
          >
            Iniciar Sesión
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
            placeholder="Correo electrónico"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />
          {mode !== "confirm" && (
            <input
              type="password"
              placeholder="Contraseña"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              minLength={8}
            />
          )}
          {mode === "confirm" && (
            <input
              type="text"
              placeholder="Código de verificación"
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
                ? "Iniciar Sesión"
                : mode === "register"
                  ? "Registrarse"
                  : "Confirmar"}
          </button>
        </form>
      </div>
    </div>
  );
}
