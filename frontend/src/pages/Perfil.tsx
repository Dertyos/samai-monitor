import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";
import { useToast } from "../hooks/useToast";
import styles from "./Perfil.module.css";

/**
 * Perfil — pagina de cuenta del usuario autenticado.
 *
 * Secciones:
 * 1. Informacion de cuenta (email readonly)
 * 2. Cambiar contraseña (old + new password)
 * 3. Zona peligrosa (cerrar sesion)
 *
 * Ruta: /perfil (protegida)
 */
export default function Perfil() {
  const navigate = useNavigate();
  const { email, signOut, changePassword } = useAuth();
  const toast = useToast();

  const [oldPassword, setOldPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const handleChangePassword = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSuccess(null);

    if (newPassword !== confirmPassword) {
      setError("Las contraseñas no coinciden");
      return;
    }

    if (newPassword.length < 8) {
      setError("La nueva contraseña debe tener al menos 8 caracteres");
      return;
    }

    setLoading(true);
    try {
      await changePassword(oldPassword, newPassword);
      setSuccess("Contraseña actualizada correctamente");
      toast.success("Contraseña actualizada");
      setOldPassword("");
      setNewPassword("");
      setConfirmPassword("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error al cambiar contraseña");
    } finally {
      setLoading(false);
    }
  };

  const handleSignOut = () => {
    signOut();
    navigate("/login", { replace: true });
  };

  return (
    <div className={styles.page}>
      <div className={styles.header}>
        <button onClick={() => navigate("/dashboard")} className="btn-back">
          &larr; Volver al dashboard
        </button>
        <h2>Mi Cuenta</h2>
      </div>

      {/* Seccion 1: Info de cuenta */}
      <section className={styles.section}>
        <h3>Información de Cuenta</h3>
        <div className={styles.infoRow}>
          <span className={styles.infoLabel}>Email</span>
          <span className={styles.infoValue}>{email}</span>
        </div>
      </section>

      {/* Seccion: Suscripcion */}
      <section className={styles.section}>
        <h3>Suscripción</h3>
        <p style={{ fontSize: "0.85rem", color: "var(--text-secondary)", marginBottom: "1rem" }}>
          Administra tu plan actual y facturación.
        </p>
        <div className={styles.infoRow} style={{ marginBottom: "0.5rem" }}>
          <span className={styles.infoLabel}>Plan actual</span>
          <span className={styles.infoValue}><strong>Gratuito</strong></span>
        </div>
        <div className={styles.actions}>
          <button className="primary" onClick={() => toast.success("Los planes premium estarán disponibles pronto")}>
            Mejorar plan
          </button>
          <button className="btn-secondary" onClick={() => toast.info("No hay historial de facturación")}>
            Ver facturas
          </button>
        </div>
      </section>

      {/* Seccion 2: Cambiar contrasena */}
      <section className={styles.section}>
        <h3>Cambiar Contraseña</h3>
        <form className={styles.passwordForm} onSubmit={handleChangePassword}>
          <input
            type="password"
            placeholder="Contraseña actual"
            value={oldPassword}
            onChange={(e) => setOldPassword(e.target.value)}
            required
          />
          <input
            type="password"
            placeholder="Nueva contraseña"
            value={newPassword}
            onChange={(e) => setNewPassword(e.target.value)}
            required
            minLength={8}
          />
          <input
            type="password"
            placeholder="Confirmar nueva contraseña"
            value={confirmPassword}
            onChange={(e) => setConfirmPassword(e.target.value)}
            required
            minLength={8}
          />
          {error && <div className="error">{error}</div>}
          {success && <div className="success-msg">{success}</div>}
          <div className={styles.actions}>
            <button type="submit" className="primary" disabled={loading}>
              {loading ? "Actualizando..." : "Cambiar contraseña"}
            </button>
          </div>
        </form>
      </section>

      {/* Seccion 3: Zona peligrosa */}
      <section className={`${styles.section} ${styles.dangerZone}`}>
        <h3>Sesion</h3>
        <p style={{ fontSize: "0.85rem", color: "var(--text-secondary)", marginBottom: "0.75rem" }}>
          Cerrar sesion en este dispositivo.
        </p>
        <button onClick={handleSignOut} className="btn-danger">
          Cerrar sesion
        </button>
      </section>
    </div>
  );
}
