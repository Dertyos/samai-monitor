import { useState, useEffect } from "react";
import { useNavigate, Link } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  getRadicados,
  addRadicado,
  deleteRadicado,
  updateRadicadoAlias,
  toggleRadicadoActivo,
  getAlertas,
  markAllAlertasRead,
  type RadicadoDTO,
} from "../lib/api";
import AddRadicadoModal from "../components/AddRadicadoModal";
import ConfirmModal from "../components/ConfirmModal";
import RadicadoCard from "../components/RadicadoCard";
import AlertasList from "../components/AlertasList";
import { useAuth } from "../hooks/useAuth";
import { useTheme } from "../hooks/useTheme";
import { useToast } from "../hooks/useToast";
import styles from "./Dashboard.module.css";

/**
 * Dashboard — pagina principal autenticada.
 *
 * Muestra los radicados del usuario, alertas recientes,
 * y permite agregar/eliminar radicados.
 * Usa ConfirmModal para confirmar eliminacion (en vez de window.confirm).
 */
export default function Dashboard() {
  const navigate = useNavigate();
  const { email, signOut } = useAuth();
  const [showAddModal, setShowAddModal] = useState(false);
  const [deleteTarget, setDeleteTarget] = useState<RadicadoDTO | null>(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [sortBy, setSortBy] = useState<"recent" | "alias" | "activo">("recent");
  const queryClient = useQueryClient();
  const { theme, toggle: toggleTheme } = useTheme();
  const toast = useToast();

  const radicadosQuery = useQuery({
    queryKey: ["radicados"],
    queryFn: getRadicados,
    staleTime: 2 * 60 * 1000, // 2 min
  });

  const alertasQuery = useQuery({
    queryKey: ["alertas"],
    queryFn: getAlertas,
    staleTime: 60 * 1000, // 1 min
  });

  const addMutation = useMutation({
    mutationFn: ({ radicado, alias }: { radicado: string; alias: string }) =>
      addRadicado(radicado, alias),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["radicados"] });
      setShowAddModal(false);
      toast.success("Radicado agregado correctamente");
    },
    onError: (err: Error) => {
      toast.error(err.message || "Error al agregar radicado");
    },
  });

  const editAliasMutation = useMutation({
    mutationFn: ({ radicado, alias }: { radicado: string; alias: string }) =>
      updateRadicadoAlias(radicado, alias),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["radicados"] });
      toast.success("Alias actualizado");
    },
    onError: (err: Error) => {
      toast.error(err.message || "Error al actualizar alias");
    },
  });

  const toggleMutation = useMutation({
    mutationFn: toggleRadicadoActivo,
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ["radicados"] });
      toast.success(data.activo ? "Monitoreo reactivado" : "Monitoreo pausado");
    },
    onError: (err: Error) => {
      toast.error(err.message || "Error al cambiar estado");
    },
  });

  const markAllReadMutation = useMutation({
    mutationFn: markAllAlertasRead,
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ["alertas"] });
      toast.success(`${data.count} alerta${data.count !== 1 ? "s" : ""} marcada${data.count !== 1 ? "s" : ""} como leida${data.count !== 1 ? "s" : ""}`);
    },
    onError: (err: Error) => {
      toast.error(err.message || "Error al marcar alertas");
    },
  });

  const deleteMutation = useMutation({
    mutationFn: deleteRadicado,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["radicados"] });
      queryClient.invalidateQueries({ queryKey: ["alertas"] });
      setDeleteTarget(null);
      toast.success("Radicado eliminado");
    },
    onError: (err: Error) => {
      toast.error(err.message || "Error al eliminar radicado");
    },
  });

  const handleSignOut = () => {
    signOut();
    navigate("/login", { replace: true });
  };

  const unreadCount = alertasQuery.data?.filter((a) => !a.leido).length ?? 0;

  useEffect(() => {
    document.title = unreadCount > 0
      ? `(${unreadCount}) SAMAI Monitor`
      : "SAMAI Monitor";
  }, [unreadCount]);

  return (
    <div className={styles.dashboard}>
      <header>
        <div>
          <h1>
            SAMAI Monitor
            {unreadCount > 0 && (
              <span className={styles.badge}>{unreadCount}</span>
            )}
          </h1>
        </div>
        <div className={styles.headerRight}>
          <Link to="/perfil" className={styles.email} title="Mi cuenta">
            {email}
          </Link>
          <button onClick={toggleTheme} className="theme-toggle" title="Cambiar tema">
            {theme === "light" ? "\u{1F319}" : "\u{2600}\u{FE0F}"}
          </button>
          <button onClick={handleSignOut} className="btn-secondary">
            Cerrar sesion
          </button>
        </div>
      </header>

      <main className={styles.main}>
        <section className={styles.section}>
          <div className={styles.sectionHeader}>
            <h2>Mis Radicados</h2>
            <button onClick={() => setShowAddModal(true)} className="primary">
              + Agregar
            </button>
          </div>

          {radicadosQuery.data && radicadosQuery.data.length > 0 && (
            <div className={styles.filterBar}>
              <input
                type="text"
                placeholder="Buscar por numero o alias..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className={styles.searchInput}
              />
              <select
                value={sortBy}
                onChange={(e) => setSortBy(e.target.value as "recent" | "alias" | "activo")}
                className={styles.sortSelect}
              >
                <option value="recent">Mas recientes</option>
                <option value="alias">Por alias (A-Z)</option>
                <option value="activo">Activos primero</option>
              </select>
            </div>
          )}

          {radicadosQuery.isLoading && (
            <div className="loading-container">
              <div className="spinner" />
              <p>Cargando radicados...</p>
            </div>
          )}
          {radicadosQuery.error && (
            <p className="error">
              Error: {radicadosQuery.error instanceof Error ? radicadosQuery.error.message : "Error"}
            </p>
          )}

          <div className={styles.radicadosGrid}>
            {radicadosQuery.data?.filter((r: RadicadoDTO) => {
              if (!searchQuery) return true;
              const q = searchQuery.toLowerCase();
              return (
                r.radicado.includes(q) ||
                r.radicadoFormato.toLowerCase().includes(q) ||
                r.alias.toLowerCase().includes(q)
              );
            }).sort((a: RadicadoDTO, b: RadicadoDTO) => {
              if (sortBy === "alias") return a.alias.localeCompare(b.alias);
              if (sortBy === "activo") return (b.activo ? 1 : 0) - (a.activo ? 1 : 0);
              return 0; // "recent" = server order
            }).map((r: RadicadoDTO) => (
              <RadicadoCard
                key={r.radicado}
                radicado={r}
                isSelected={false}
                onSelect={() => navigate(`/radicado/${r.radicado}`)}
                onDelete={() => setDeleteTarget(r)}
                onEditAlias={(alias) => editAliasMutation.mutate({ radicado: r.radicado, alias })}
                onToggleActivo={() => toggleMutation.mutate(r.radicado)}
                isDeleting={
                  deleteMutation.isPending &&
                  deleteMutation.variables === r.radicado
                }
                isEditing={
                  editAliasMutation.isPending &&
                  editAliasMutation.variables?.radicado === r.radicado
                }
                isToggling={
                  toggleMutation.isPending &&
                  toggleMutation.variables === r.radicado
                }
              />
            ))}
            {radicadosQuery.data?.length === 0 && (
              <div className="empty-state">
                <p className="empty-state-icon">&#x1F4CB;</p>
                <p className="empty-state-text">No tienes radicados monitoreados</p>
                <p className="empty-state-hint">Agrega uno con el boton "+ Agregar" para empezar</p>
              </div>
            )}
          </div>
        </section>

        <section className={styles.section}>
          <div className={styles.sectionHeader}>
            <h2>Alertas Recientes</h2>
            {alertasQuery.data && alertasQuery.data.some((a) => !a.leido) && (
              <button
                onClick={() => markAllReadMutation.mutate()}
                className="btn-secondary"
                disabled={markAllReadMutation.isPending}
              >
                {markAllReadMutation.isPending ? "..." : "Marcar todas leidas"}
              </button>
            )}
          </div>
          {alertasQuery.isLoading && (
            <div className="loading-container">
              <div className="spinner" />
              <p>Cargando alertas...</p>
            </div>
          )}
          {alertasQuery.data && <AlertasList alertas={alertasQuery.data} />}
          {alertasQuery.data?.length === 0 && (
            <div className="empty-state">
              <p className="empty-state-icon">&#x1F514;</p>
              <p className="empty-state-text">Sin alertas recientes</p>
              <p className="empty-state-hint">Las alertas aparecen cuando el monitor detecta nuevas actuaciones</p>
            </div>
          )}
        </section>
      </main>

      {showAddModal && (
        <AddRadicadoModal
          onAdd={(radicado, alias) => addMutation.mutate({ radicado, alias })}
          onClose={() => setShowAddModal(false)}
          error={
            addMutation.error instanceof Error
              ? addMutation.error.message
              : null
          }
          loading={addMutation.isPending}
        />
      )}

      {deleteTarget && (
        <ConfirmModal
          title="Dejar de monitorear"
          message={`Se eliminara el radicado ${deleteTarget.radicadoFormato}${deleteTarget.alias ? ` (${deleteTarget.alias})` : ""} y todas sus alertas asociadas.`}
          confirmLabel="Eliminar"
          variant="danger"
          onConfirm={() => deleteMutation.mutate(deleteTarget.radicado)}
          onCancel={() => setDeleteTarget(null)}
          loading={deleteMutation.isPending}
        />
      )}
    </div>
  );
}
