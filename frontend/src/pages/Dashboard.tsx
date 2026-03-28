import { useState, useEffect, useMemo } from "react";
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
import AppLogo from "../components/AppLogo";
import { RadicadoCardSkeleton, StatsBarSkeleton } from "../components/Skeleton";
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
  const [sortBy, setSortBy] = useState<"recent" | "alias" | "activo" | "numero">(
    () => (localStorage.getItem("sortBy") as "recent" | "alias" | "activo" | "numero") ?? "recent"
  );
  const [sortDir, setSortDir] = useState<"asc" | "desc">(
    () => (localStorage.getItem("sortDir") as "asc" | "desc") ?? "desc"
  );
  const handleSetSortBy = (sort: "recent" | "alias" | "activo" | "numero") => {
    localStorage.setItem("sortBy", sort);
    setSortBy(sort);
  };
  const handleToggleSortDir = () => {
    const next = sortDir === "asc" ? "desc" : "asc";
    localStorage.setItem("sortDir", next);
    setSortDir(next);
  };
  const [showHistorial, setShowHistorial] = useState(false);
  const isMobile = window.innerWidth <= 640;
  const [viewMode, setViewMode] = useState<"grid" | "list">(
    () => isMobile ? "list" : ((localStorage.getItem("viewMode") as "grid" | "list") ?? "grid")
  );
  const handleSetViewMode = (mode: "grid" | "list") => {
    localStorage.setItem("viewMode", mode);
    setViewMode(mode);
  };
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
    refetchInterval: 60 * 1000, // poll cada 60s para detectar alertas nuevas
  });

  const filteredRadicados = useMemo(() => {
    if (!radicadosQuery.data) return [];
    return radicadosQuery.data
      .filter((r: RadicadoDTO) => {
        if (!searchQuery) return true;
        const q = searchQuery.toLowerCase();
        return (
          r.radicado.includes(q) ||
          r.radicadoFormato.toLowerCase().includes(q) ||
          r.alias.toLowerCase().includes(q)
        );
      })
      .sort((a: RadicadoDTO, b: RadicadoDTO) => {
        let cmp = 0;
        if (sortBy === "alias") cmp = a.alias.localeCompare(b.alias);
        else if (sortBy === "activo") cmp = (b.activo ? 1 : 0) - (a.activo ? 1 : 0);
        else if (sortBy === "numero") cmp = a.radicado.localeCompare(b.radicado);
        else if (sortBy === "recent") {
          const fa = a.fechaUltimaActuacion || a.createdAt || "";
          const fb = b.fechaUltimaActuacion || b.createdAt || "";
          cmp = fa.localeCompare(fb);
        }
        return sortDir === "asc" ? cmp : -cmp;
      });
  }, [radicadosQuery.data, searchQuery, sortBy, sortDir]);

  const addMutation = useMutation({
    mutationFn: ({ radicado, alias, fuente, idProceso }: { radicado: string; alias: string; fuente: string; idProceso?: number }) =>
      addRadicado(radicado, alias, fuente, idProceso),
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

  const unreadAlertas = useMemo(
    () => alertasQuery.data?.filter((a) => !a.leido) ?? [],
    [alertasQuery.data],
  );
  const readAlertas = useMemo(
    () => alertasQuery.data?.filter((a) => a.leido) ?? [],
    [alertasQuery.data],
  );
  const unreadCount = unreadAlertas.length;

  useEffect(() => {
    document.title = unreadCount > 0
      ? `(${unreadCount}) Alertas Judiciales`
      : "Alertas Judiciales";
  }, [unreadCount]);

  return (
    <div className={styles.dashboard}>
      <header>
        <div className={styles.headerBrand}>
          <AppLogo size={32} />
          <h1>
            Alertas Judiciales
            {unreadCount > 0 && (
              <span className={styles.badge}>{unreadCount}</span>
            )}
            <br /><small>by Dertyos</small>
          </h1>
        </div>
        <div className={styles.headerRight}>
          <Link to="/perfil" className={styles.email} title="Mi cuenta">
            {email}
          </Link>
          <button
            onClick={toggleTheme}
            className="theme-toggle"
            title={theme === "light" ? "Cambiar a modo oscuro" : "Cambiar a modo claro"}
            aria-label={theme === "light" ? "Cambiar a modo oscuro" : "Cambiar a modo claro"}
          >
            {theme === "light" ? "\u{1F319}" : "\u{2600}\u{FE0F}"}
          </button>
          <button onClick={handleSignOut} className="btn-secondary">
            Cerrar sesion
          </button>
        </div>
      </header>

      <main className={styles.main}>
        {radicadosQuery.isLoading && <StatsBarSkeleton />}
        {radicadosQuery.data && (
          <div className={styles.statsBar}>
            <div className={styles.stat}>
              <span className={styles.statValue}>{radicadosQuery.data.length}</span>
              <span className={styles.statLabel}>Radicados</span>
            </div>
            <div className={styles.stat}>
              <span className={styles.statValue}>
                {radicadosQuery.data.filter((r) => r.activo).length}
              </span>
              <span className={styles.statLabel}>Activos</span>
            </div>
            <div className={styles.stat}>
              <span className={styles.statValue}>{unreadCount}</span>
              <span className={styles.statLabel}>Alertas nuevas</span>
            </div>
          </div>
        )}

        <section className={styles.section}>
          <div className={styles.sectionHeader}>
            <h2>Mis Radicados</h2>
            <div className={styles.sectionActions}>
              <div className={styles.viewToggle}>
                <button
                  className={`${styles.viewToggleBtn} ${viewMode === "grid" ? styles.viewToggleBtnActive : ""}`}
                  onClick={() => handleSetViewMode("grid")}
                  title="Vista tarjetas"
                  aria-label="Vista tarjetas"
                  aria-pressed={viewMode === "grid"}
                >
                  <svg width="15" height="15" viewBox="0 0 16 16" fill="currentColor" aria-hidden="true">
                    <rect x="1" y="1" width="6" height="6" rx="1"/>
                    <rect x="9" y="1" width="6" height="6" rx="1"/>
                    <rect x="1" y="9" width="6" height="6" rx="1"/>
                    <rect x="9" y="9" width="6" height="6" rx="1"/>
                  </svg>
                </button>
                <button
                  className={`${styles.viewToggleBtn} ${viewMode === "list" ? styles.viewToggleBtnActive : ""}`}
                  onClick={() => handleSetViewMode("list")}
                  title="Vista lista"
                  aria-label="Vista lista"
                  aria-pressed={viewMode === "list"}
                >
                  <svg width="15" height="15" viewBox="0 0 16 16" fill="currentColor" aria-hidden="true">
                    <rect x="1" y="2" width="14" height="2" rx="1"/>
                    <rect x="1" y="7" width="14" height="2" rx="1"/>
                    <rect x="1" y="12" width="14" height="2" rx="1"/>
                  </svg>
                </button>
              </div>
              <button onClick={() => setShowAddModal(true)} className="primary">
                + Agregar
              </button>
            </div>
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
              <div className={styles.sortGroup}>
                <select
                  value={sortBy}
                  onChange={(e) => handleSetSortBy(e.target.value as "recent" | "alias" | "activo" | "numero")}
                  className={styles.sortSelect}
                >
                  <option value="recent">Mas recientes</option>
                  <option value="alias">Por alias</option>
                  <option value="activo">Activos primero</option>
                  <option value="numero">Por número</option>
                </select>
                <button
                  onClick={handleToggleSortDir}
                  className={styles.sortDirBtn}
                  title={sortDir === "asc" ? "Cambiar a descendente" : "Cambiar a ascendente"}
                >
                  {sortDir === "asc" ? "↑" : "↓"}
                </button>
              </div>
            </div>
          )}

          {radicadosQuery.isLoading && (
            <div className={viewMode === "grid" ? styles.radicadosGrid : styles.radicadosList}>
              {[0, 1, 2].map((i) => <RadicadoCardSkeleton key={i} />)}
            </div>
          )}
          {radicadosQuery.error && (
            <p className="error">
              Error: {radicadosQuery.error instanceof Error ? radicadosQuery.error.message : "Error"}
            </p>
          )}

          {radicadosQuery.data?.length === 0 && !searchQuery ? (
            <div className={styles.onboarding}>
              <h3 className={styles.onboardingTitle}>Bienvenido a Alertas Judiciales</h3>
              <p className={styles.onboardingSubtitle}>Monitorea tus procesos en SAMAI y Rama Judicial. Recibe alertas cuando haya nuevas actuaciones.</p>
              <div className={styles.onboardingSteps}>
                <div className={styles.onboardingStep}>
                  <span className={styles.onboardingStepNum}>1</span>
                  <div>
                    <strong>Agrega un radicado</strong>
                    <p>Haz clic en "+ Agregar" e ingresa el numero de tu proceso. Puedes buscarlo por nombre o numero parcial.</p>
                  </div>
                </div>
                <div className={styles.onboardingStep}>
                  <span className={styles.onboardingStepNum}>2</span>
                  <div>
                    <strong>El sistema lo monitorea</strong>
                    <p>Cada dia el monitor consulta SAMAI y Rama Judicial para detectar nuevas actuaciones automaticamente.</p>
                  </div>
                </div>
                <div className={styles.onboardingStep}>
                  <span className={styles.onboardingStepNum}>3</span>
                  <div>
                    <strong>Recibe alertas</strong>
                    <p>Cuando haya actuaciones nuevas te avisamos aqui y por correo electronico.</p>
                  </div>
                </div>
              </div>
              <button onClick={() => setShowAddModal(true)} className="primary" style={{ marginTop: "1.5rem" }}>
                + Agregar primer radicado
              </button>
            </div>
          ) : searchQuery && filteredRadicados.length === 0 && (radicadosQuery.data?.length ?? 0) > 0 ? (
            <div className="empty-state">
              <div className="empty-state-icon">
                <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                  <circle cx="11" cy="11" r="8"/>
                  <line x1="21" y1="21" x2="16.65" y2="16.65"/>
                  <line x1="8" y1="11" x2="14" y2="11"/>
                </svg>
              </div>
              <p className="empty-state-text">Sin resultados para "{searchQuery}"</p>
              <p className="empty-state-hint">Intenta con otro termino de busqueda</p>
            </div>
          ) : (
            <div className={viewMode === "grid" ? styles.radicadosGrid : styles.radicadosList}>
              {filteredRadicados.map((r: RadicadoDTO) => (
                <RadicadoCard
                  key={r.radicado}
                  radicado={r}
                  isSelected={false}
                  listMode={viewMode === "list"}
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
            </div>
          )}
        </section>

        <section className={styles.section}>
          <div className={styles.sectionHeader}>
            <h2>Alertas Recientes</h2>
            <div className={styles.alertasActions}>
              {alertasQuery.dataUpdatedAt > 0 && (
                <span className={styles.lastUpdated}>
                  Actualizado {new Date(alertasQuery.dataUpdatedAt).toLocaleTimeString("es-CO", { hour: "2-digit", minute: "2-digit" })}
                </span>
              )}
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
          </div>
          {alertasQuery.isLoading && (
            <div className="loading-container">
              <div className="spinner" />
              <p>Cargando alertas...</p>
            </div>
          )}
          {alertasQuery.data && unreadCount > 0 && (
            <AlertasList alertas={unreadAlertas} />
          )}
          {alertasQuery.data && unreadCount === 0 && (
            <div className="empty-state">
              <div className="empty-state-icon">
                <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                  <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/>
                  <polyline points="22 4 12 14.01 9 11.01"/>
                </svg>
              </div>
              <p className="empty-state-text">Estas al dia</p>
              <p className="empty-state-hint">Las alertas aparecen cuando el monitor detecta nuevas actuaciones.</p>
            </div>
          )}
        </section>

        {/* Historial de alertas leidas */}
        {readAlertas.length > 0 && (
          <section className={styles.section}>
            <div className={styles.sectionHeader}>
              <button
                className={styles.historialToggle}
                onClick={() => setShowHistorial((v) => !v)}
                aria-expanded={showHistorial}
              >
                <span className={styles.historialChevron}>{showHistorial ? "▾" : "▸"}</span>
                Historial leido
                <span className={styles.historialCount}>{readAlertas.length}</span>
              </button>
            </div>
            {showHistorial && (
              <AlertasList alertas={readAlertas} historialMode />
            )}
          </section>
        )}
      </main>

      {showAddModal && (
        <AddRadicadoModal
          onAdd={(radicado, alias, fuente, idProceso) => addMutation.mutate({ radicado, alias, fuente, idProceso })}
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
