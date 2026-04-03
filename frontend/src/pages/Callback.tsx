import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { handleOAuthCallback } from "../lib/cognito";

export default function Callback() {
  const navigate = useNavigate();
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    try {
      handleOAuthCallback(window.location.hash);
      navigate("/dashboard", { replace: true });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error de autenticacion");
    }
  }, [navigate]);

  if (error) {
    return (
      <div className="loading-screen">
        <h1>Alertas Judiciales<br /><small>by Dertyos</small></h1>
        <p className="error">{error}</p>
        <button className="primary" onClick={() => navigate("/login", { replace: true })}>
          Volver al login
        </button>
      </div>
    );
  }

  return (
    <div className="loading-screen">
      <h1>Alertas Judiciales<br /><small>by Dertyos</small></h1>
      <div className="spinner" />
      <p>Iniciando sesion...</p>
    </div>
  );
}
