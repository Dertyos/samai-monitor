import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";
import { useToast } from "../hooks/useToast";
import { deleteCuenta, getBillingStatus } from "../lib/api";
import { useQuery } from "@tanstack/react-query";
import ConfirmModal from "../components/ConfirmModal";
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
  const billingQuery = useQuery({
    queryKey: ["billing-status"],
    queryFn: getBillingStatus,
    staleTime: 5 * 60 * 1000,
  });
  const { email, signOut, changePassword } = useAuth();
  const toast = useToast();

  const [oldPassword, setOldPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [deleting, setDeleting] = useState(false);

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
        <h3>Suscripcion</h3>
        <p style={{ fontSize: "0.85rem", color: "var(--text-secondary)", marginBottom: "1rem" }}>
          Administra tu plan actual y facturacion.
        </p>
        <div className={styles.infoRow} style={{ marginBottom: "0.5rem" }}>
          <span className={styles.infoLabel}>Plan actual</span>
          <span className={styles.infoValue}>
            <strong>{billingQuery.data?.planName ?? "Gratuito"}</strong>
          </span>
        </div>
        {billingQuery.data && (
          <div className={styles.infoRow} style={{ marginBottom: "0.5rem" }}>
            <span className={styles.infoLabel}>Uso</span>
            <span className={styles.infoValue}>
              {billingQuery.data.processCount}/{billingQuery.data.processLimit} procesos
            </span>
          </div>
        )}
        <div className={styles.actions}>
          <button className="primary" onClick={() => navigate("/billing")}>
            Administrar suscripcion
          </button>
          <button className="btn-secondary" onClick={() => navigate("/planes")}>
            Ver planes
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
        <h3>Zona peligrosa</h3>
        <p style={{ fontSize: "0.85rem", color: "var(--text-secondary)", marginBottom: "0.75rem" }}>
          Cerrar sesion en este dispositivo.
        </p>
        <button onClick={handleSignOut} className="btn-danger">
          Cerrar sesion
        </button>

        <hr style={{ border: "none", borderTop: "1px solid var(--border)", margin: "1rem 0" }} />

        <p style={{ fontSize: "0.85rem", color: "var(--text-secondary)", marginBottom: "0.75rem" }}>
          Eliminar permanentemente tu cuenta y todos tus datos (radicados, alertas, etiquetas).
          Esta accion no se puede deshacer.
        </p>
        <button onClick={() => setShowDeleteModal(true)} className="btn-danger">
          Eliminar mi cuenta
        </button>
      </section>

      {showDeleteModal && (
        <ConfirmModal
          title="Eliminar cuenta"
          message={`Se eliminara permanentemente la cuenta ${email} y todos sus datos. Esta accion no se puede deshacer.`}
          confirmLabel="Eliminar cuenta"
          variant="danger"
          loading={deleting}
          onCancel={() => setShowDeleteModal(false)}
          onConfirm={async () => {
            setDeleting(true);
            try {
              await deleteCuenta();
              signOut();
              navigate("/login", { replace: true });
            } catch (err) {
              toast.error(err instanceof Error ? err.message : "Error eliminando cuenta");
              setDeleting(false);
              setShowDeleteModal(false);
            }
          }}
        />
      )}
    </div>
  );
}
