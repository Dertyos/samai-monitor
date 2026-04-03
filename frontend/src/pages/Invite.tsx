import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";
import { useToast } from "../hooks/useToast";
import { API_URL } from "../config/auth";
import { getIdToken } from "../lib/cognito";

interface InvitationInfo {
  token: string;
  teamName: string;
  email: string;
  status: string;
}

export default function Invite() {
  const { token } = useParams<{ token: string }>();
  const navigate = useNavigate();
  const { isAuthenticated, isLoading: authLoading } = useAuth();
  const toast = useToast();

  const [invitation, setInvitation] = useState<InvitationInfo | null>(null);
  const [loading, setLoading] = useState(true);
  const [accepting, setAccepting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!token) return;
    fetch(`${API_URL}/invitations/${token}`)
      .then((res) => {
        if (!res.ok) throw new Error("Invitacion no encontrada o expirada");
        return res.json();
      })
      .then(setInvitation)
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, [token]);

  const handleAccept = async () => {
    if (!token) return;
    setAccepting(true);
    try {
      const idToken = await getIdToken();
      const res = await fetch(`${API_URL}/invitations/${token}/accept`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${idToken}`,
        },
      });
      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        throw new Error(body.error || "Error al aceptar");
      }
      const data = await res.json();
      if (data.status === "already_member") {
        toast.success("Ya eres miembro de este equipo");
      } else {
        toast.success(`Te uniste al equipo ${data.teamName}`);
      }
      navigate("/dashboard");
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Error");
      setAccepting(false);
    }
  };

  if (loading || authLoading) {
    return (
      <div style={{ display: "flex", justifyContent: "center", alignItems: "center", minHeight: "100vh" }}>
        <div className="spinner" />
      </div>
    );
  }

  if (error || !invitation) {
    return (
      <div style={{ display: "flex", flexDirection: "column", justifyContent: "center", alignItems: "center", minHeight: "100vh", gap: "1rem" }}>
        <h2>Invitacion no valida</h2>
        <p style={{ color: "var(--text-secondary)" }}>{error || "La invitacion no existe o ya expiro."}</p>
        <button className="primary" onClick={() => navigate("/login")}>
          Ir al inicio
        </button>
      </div>
    );
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", justifyContent: "center", alignItems: "center", minHeight: "100vh", gap: "1.5rem", padding: "2rem" }}>
      <h1>Invitacion a equipo</h1>
      <div style={{
        background: "var(--bg-card, #fff)",
        border: "1px solid var(--border, #e5e7eb)",
        borderRadius: "0.75rem",
        padding: "2rem",
        maxWidth: "400px",
        width: "100%",
        textAlign: "center",
      }}>
        <h2 style={{ marginBottom: "0.5rem" }}>{invitation.teamName}</h2>
        <p style={{ color: "var(--text-secondary)", marginBottom: "1.5rem" }}>
          Te invitaron a unirte a este equipo en Alertas Judiciales.
        </p>

        {isAuthenticated ? (
          <button
            className="primary"
            onClick={handleAccept}
            disabled={accepting}
            style={{ width: "100%" }}
          >
            {accepting ? "Aceptando..." : "Aceptar invitacion"}
          </button>
        ) : (
          <>
            <p style={{ fontSize: "0.85rem", color: "var(--text-secondary)", marginBottom: "1rem" }}>
              Necesitas una cuenta para unirte. Registrate con el email <strong>{invitation.email}</strong>.
            </p>
            <button
              className="primary"
              onClick={() => navigate(`/login?invite=${token}`)}
              style={{ width: "100%" }}
            >
              Registrarse / Iniciar sesion
            </button>
          </>
        )}
      </div>
    </div>
  );
}
