import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";
import { useToast } from "../hooks/useToast";
import { deleteCuenta, getBillingStatus, getTeams, createTeam, addTeamMember, removeTeamMember, type TeamDTO } from "../lib/api";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
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
  const queryClient = useQueryClient();
  const billingQuery = useQuery({
    queryKey: ["billing-status"],
    queryFn: getBillingStatus,
    staleTime: 5 * 60 * 1000,
  });
  const teamsQuery = useQuery({
    queryKey: ["teams"],
    queryFn: getTeams,
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

  // Team state
  const [teamName, setTeamName] = useState("");
  const [inviteEmail, setInviteEmail] = useState("");

  const createTeamMutation = useMutation({
    mutationFn: (name: string) => createTeam(name),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["teams"] });
      setTeamName("");
      toast.success("Equipo creado");
    },
    onError: (err: Error) => toast.error(err.message),
  });

  const addMemberMutation = useMutation({
    mutationFn: ({ teamId, memberEmail }: { teamId: string; memberEmail: string }) => addTeamMember(teamId, memberEmail),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ["teams"] });
      setInviteEmail("");
      if (data.invited) {
        toast.success(`Invitacion enviada a ${data.email}. Expira en 7 dias.`);
      } else {
        toast.success("Miembro agregado");
      }
    },
    onError: (err: Error) => toast.error(err.message),
  });

  const removeMemberMutation = useMutation({
    mutationFn: ({ teamId, uid }: { teamId: string; uid: string }) => removeTeamMember(teamId, uid),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["teams"] });
      toast.success("Miembro removido");
    },
    onError: (err: Error) => toast.error(err.message),
  });

  const myTeam: TeamDTO | undefined = teamsQuery.data?.[0];
  // Planes que permiten equipos: Firma y Enterprise
  const hasTeamPlan = billingQuery.data?.plan === "plan-firma" || billingQuery.data?.plan === "plan-enterprise";

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

      {/* Seccion: Mi Equipo */}
      {(hasTeamPlan || myTeam) && (
        <section className={styles.section}>
          <h3>Mi Equipo</h3>
          <p style={{ fontSize: "0.85rem", color: "var(--text-secondary)", marginBottom: "1rem" }}>
            Comparte tu plan Firma o Enterprise con hasta 5 usuarios. Los radicados compartidos cuentan una sola vez.
          </p>

          {!myTeam ? (
            <form onSubmit={(e) => { e.preventDefault(); if (teamName.trim()) createTeamMutation.mutate(teamName.trim()); }}>
              <label>
                Nombre del equipo
                <input
                  type="text"
                  placeholder="Ej: Firma Aviles & Asoc."
                  value={teamName}
                  onChange={(e) => setTeamName(e.target.value)}
                  required
                />
              </label>
              <div className={styles.actions}>
                <button type="submit" className="primary" disabled={createTeamMutation.isPending || !teamName.trim()}>
                  {createTeamMutation.isPending ? "Creando..." : "Crear equipo"}
                </button>
              </div>
            </form>
          ) : (
            <>
              <div className={styles.infoRow} style={{ marginBottom: "0.5rem" }}>
                <span className={styles.infoLabel}>Equipo</span>
                <span className={styles.infoValue}><strong>{myTeam.name}</strong></span>
              </div>
              <div className={styles.infoRow} style={{ marginBottom: "0.5rem" }}>
                <span className={styles.infoLabel}>Estado</span>
                <span className={styles.infoValue}>
                  {myTeam.active
                    ? <span style={{ color: "var(--color-success, #22c55e)" }}>Activo</span>
                    : <span style={{ color: "var(--color-danger, #ef4444)" }}>Inhabilitado (suscripcion vencida)</span>
                  }
                </span>
              </div>
              <div className={styles.infoRow} style={{ marginBottom: "1rem" }}>
                <span className={styles.infoLabel}>Procesos</span>
                <span className={styles.infoValue}>{myTeam.processCount}/{myTeam.processLimit}</span>
              </div>

              {/* Lista de miembros */}
              {myTeam.members.length > 0 && (
                <div style={{ marginBottom: "1rem" }}>
                  <strong style={{ fontSize: "0.85rem" }}>Miembros ({myTeam.members.length}/5)</strong>
                  <ul style={{ listStyle: "none", padding: 0, margin: "0.5rem 0" }}>
                    {myTeam.members.map((m) => (
                      <li key={m.userId} style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "0.35rem 0", fontSize: "0.85rem" }}>
                        <span>
                          {m.userId}
                          {m.role === "owner" && <span style={{ marginLeft: "0.5rem", color: "var(--text-secondary)", fontSize: "0.75rem" }}>(dueno)</span>}
                        </span>
                        {m.role !== "owner" && myTeam.active && (
                          <button
                            type="button"
                            className="btn-danger"
                            style={{ fontSize: "0.75rem", padding: "0.15rem 0.5rem" }}
                            onClick={() => removeMemberMutation.mutate({ teamId: myTeam.teamId, uid: m.userId })}
                            disabled={removeMemberMutation.isPending}
                          >
                            Quitar
                          </button>
                        )}
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Invitaciones pendientes */}
              {myTeam.pendingInvitations && myTeam.pendingInvitations.length > 0 && (
                <div style={{ marginBottom: "1rem" }}>
                  <strong style={{ fontSize: "0.85rem" }}>Invitaciones pendientes</strong>
                  <ul style={{ listStyle: "none", padding: 0, margin: "0.5rem 0" }}>
                    {myTeam.pendingInvitations.map((inv) => (
                      <li key={inv.inviteId} style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "0.35rem 0", fontSize: "0.85rem" }}>
                        <span style={{ color: "var(--text-secondary)" }}>
                          {inv.email}
                          <span style={{ marginLeft: "0.5rem", fontSize: "0.75rem" }}>(pendiente)</span>
                        </span>
                        <button
                          type="button"
                          className="primary"
                          style={{ fontSize: "0.75rem", padding: "0.15rem 0.5rem" }}
                          onClick={() => addMemberMutation.mutate({ teamId: myTeam.teamId, memberEmail: inv.email })}
                          disabled={addMemberMutation.isPending}
                        >
                          Reenviar
                        </button>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Invite member form — only if team is active */}
              {myTeam.active && (
                <form
                  onSubmit={(e) => {
                    e.preventDefault();
                    if (inviteEmail.trim()) addMemberMutation.mutate({ teamId: myTeam.teamId, memberEmail: inviteEmail.trim() });
                  }}
                  style={{ marginBottom: "1rem" }}
                >
                  <label>
                    Invitar miembro por email
                    <div style={{ display: "flex", gap: "0.5rem" }}>
                      <input
                        type="email"
                        placeholder="colega@firma.com"
                        value={inviteEmail}
                        onChange={(e) => setInviteEmail(e.target.value)}
                        required
                      />
                      <button type="submit" className="primary" disabled={addMemberMutation.isPending || !inviteEmail.trim()}>
                        {addMemberMutation.isPending ? "..." : "Invitar"}
                      </button>
                    </div>
                  </label>
                </form>
              )}

              {!myTeam.active && (
                <div style={{ padding: "0.75rem", background: "var(--bg-warning, #fef3c7)", borderRadius: "0.5rem", fontSize: "0.85rem", marginBottom: "1rem" }}>
                  El equipo esta inhabilitado porque la suscripcion del dueno vencio.
                  Cada miembro conserva solo sus primeros 5 radicados (plan gratuito).
                  <div className={styles.actions} style={{ marginTop: "0.5rem" }}>
                    <button className="primary" onClick={() => navigate("/billing")}>
                      Renovar suscripcion
                    </button>
                  </div>
                </div>
              )}
            </>
          )}
        </section>
      )}

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
