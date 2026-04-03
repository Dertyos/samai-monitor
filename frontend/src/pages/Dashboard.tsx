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
  getEtiquetas,
  createEtiqueta,
  updateEtiqueta,
  deleteEtiqueta,
  updateRadicadoEtiquetas,
  getBillingStatus,
  getTeams,
  confirmTeam,
  type RadicadoDTO,
  type EtiquetaDTO,
  type AddRadicadoMeta,
} from "../lib/api";
import AddRadicadoModal from "../components/AddRadicadoModal";
import ConfirmModal from "../components/ConfirmModal";
import EtiquetaManager from "../components/EtiquetaManager";
import EtiquetaFilter from "../components/EtiquetaFilter";
import RadicadoCard from "../components/RadicadoCard";
import AlertasList from "../components/AlertasList";
import AppLogo from "../components/AppLogo";
import FilterBar from "../components/FilterBar";
import { RadicadoCardSkeleton, StatsBarSkeleton } from "../components/Skeleton";
import { useAuth } from "../hooks/useAuth";
import { useTheme } from "../hooks/useTheme";
import { useToast } from "../hooks/useToast";
import { useFilters, useFilterOptions } from "../hooks/useFilters";
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
  const { signOut } = useAuth();
  const [showAddModal, setShowAddModal] = useState(false);
  const [showEtiquetaManager, setShowEtiquetaManager] = useState(false);
  const [deleteTarget, setDeleteTarget] = useState<RadicadoDTO | null>(null);
  const [filterEtiqueta, setFilterEtiqueta] = useState<string[]>([]);
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
  const { filters, setFilter, toggleArrayFilter, clearAll: clearFilters, activeCount: filterCount, hasFilters, applyFilters } = useFilters();

  const radicadosQuery = useQuery({
    queryKey: ["radicados"],
    queryFn: getRadicados,
    staleTime: 2 * 60 * 1000, // 2 min
  });

  const billingQuery = useQuery({
    queryKey: ["billing-status"],
    queryFn: getBillingStatus,
    staleTime: 5 * 60 * 1000, // 5 min
  });

  const filterOptions = useFilterOptions(radicadosQuery.data || []);

  const alertasQuery = useQuery({
    queryKey: ["alertas"],
    queryFn: getAlertas,
    staleTime: 60 * 1000, // 1 min
    refetchInterval: 60 * 1000, // poll cada 60s para detectar alertas nuevas
  });

  const etiquetasQuery = useQuery({
    queryKey: ["etiquetas"],
    queryFn: getEtiquetas,
    staleTime: 5 * 60 * 1000, // 5 min
  });

  const teamsQuery = useQuery({
    queryKey: ["teams"],
    queryFn: getTeams,
    staleTime: 60 * 1000, // 1 min — se refresca rápido post-pago
  });

  const pendingTeam = teamsQuery.data?.find(t => t.active && t.pendingConfirmation);

  const confirmTeamMutation = useMutation({
    mutationFn: (teamId: string) => confirmTeam(teamId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["teams"] });
      queryClient.invalidateQueries({ queryKey: ["radicados"] });
      toast.success("Equipo confirmado. Los radicados de los miembros se estan reactivando.");
    },
    onError: (err: Error) => toast.error(err.message),
  });

  const etiquetasMap = useMemo(() => {
    const map = new Map<string, EtiquetaDTO>();
    for (const e of etiquetasQuery.data || []) {
      map.set(e.etiquetaId, e);
    }
    return map;
  }, [etiquetasQuery.data]);

  const hasMixedActivo = useMemo(() => {
    if (!radicadosQuery.data) return false;
    return radicadosQuery.data.some((r) => r.activo) && radicadosQuery.data.some((r) => !r.activo);
  }, [radicadosQuery.data]);

  const hasAlias = useMemo(() => {
    if (!radicadosQuery.data) return false;
    return radicadosQuery.data.some((r) => r.alias.trim() !== "");
  }, [radicadosQuery.data]);

  const filteredRadicados = useMemo(() => {
    if (!radicadosQuery.data) return [];
    // Apply structured filters first, then text search, then sort
    return applyFilters(radicadosQuery.data)
      .filter((r: RadicadoDTO) => {
        // Filtro por etiqueta
        if (filterEtiqueta.length > 0 && !filterEtiqueta.some((id) => (r.etiquetas || []).includes(id))) return false;
        if (!searchQuery) return true;
        const q = searchQuery.toLowerCase();
        return (
          r.radicado.includes(q) ||
          r.radicadoFormato.toLowerCase().includes(q) ||
          r.alias.toLowerCase().includes(q) ||
          (r.despacho || "").toLowerCase().includes(q) ||
          (r.ciudad || "").toLowerCase().includes(q)
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
  }, [radicadosQuery.data, searchQuery, sortBy, sortDir, filterEtiqueta, applyFilters]);

  const addMutation = useMutation({
    mutationFn: ({ radicado, alias, fuente, idProceso, meta }: { radicado: string; alias: string; fuente: string; idProceso?: number; meta?: AddRadicadoMeta }) =>
      addRadicado(radicado, alias, fuente, idProceso, meta),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["radicados"] });
      setShowAddModal(false);
      toast.success("Radicado agregado correctamente");
    },
    onError: (err: Error) => {
      if (err.message.includes("límite") || err.message.includes("PLAN_LIMIT")) {
        toast.error("Limite de plan alcanzado. Upgrade para agregar mas procesos.");
        navigate("/billing");
        return;
      }
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

  const createEtiquetaMutation = useMutation({
    mutationFn: ({ nombre, color }: { nombre: string; color: string }) =>
      createEtiqueta(nombre, color),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["etiquetas"] });
      toast.success("Etiqueta creada");
    },
    onError: (err: Error) => {
      toast.error(err.message || "Error al crear etiqueta");
    },
  });

  const updateEtiquetaMutation = useMutation({
    mutationFn: ({ etiquetaId, nombre, color }: { etiquetaId: string; nombre: string; color: string }) =>
      updateEtiqueta(etiquetaId, nombre, color),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["etiquetas"] });
      toast.success("Etiqueta actualizada");
    },
    onError: (err: Error) => {
      toast.error(err.message || "Error al actualizar etiqueta");
    },
  });

  const deleteEtiquetaMutation = useMutation({
    mutationFn: deleteEtiqueta,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["etiquetas"] });
      queryClient.invalidateQueries({ queryKey: ["radicados"] });
      toast.success("Etiqueta eliminada");
    },
    onError: (err: Error) => {
      toast.error(err.message || "Error al eliminar etiqueta");
    },
  });

  const toggleEtiquetaRadicadoMutation = useMutation({
    mutationFn: ({ radicado, etiquetas }: { radicado: string; etiquetas: string[] }) =>
      updateRadicadoEtiquetas(radicado, etiquetas),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["radicados"] });
    },
    onError: (err: Error) => {
      toast.error(err.message || "Error al actualizar etiquetas");
    },
  });

  const handleToggleEtiqueta = (radicado: RadicadoDTO, etiquetaId: string, selected: boolean) => {
    const current = radicado.etiquetas || [];
    const next = selected
      ? [...current, etiquetaId]
      : current.filter((id) => id !== etiquetaId);
    toggleEtiquetaRadicadoMutation.mutate({ radicado: radicado.radicado, etiquetas: next });
  };

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
          <Link to="/perfil" className="btn-secondary" style={{ textDecoration: 'none' }} title="Mi cuenta">
            Mi Perfil
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
        {pendingTeam && (
          <div style={{
            padding: "1rem",
            marginBottom: "1rem",
            background: "var(--bg-warning, #fef3c7)",
            borderRadius: "0.5rem",
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            gap: "1rem",
            flexWrap: "wrap",
          }}>
            <div>
              <strong>Tu suscripcion esta activa.</strong>{" "}
              Tu equipo &quot;{pendingTeam.name}&quot; tiene {pendingTeam.members.length} miembros.
              Confirma para reactivar los radicados de todos.
            </div>
            <div style={{ display: "flex", gap: "0.5rem", flexShrink: 0 }}>
              <button
                className="primary"
                onClick={() => confirmTeamMutation.mutate(pendingTeam.teamId)}
                disabled={confirmTeamMutation.isPending}
              >
                {confirmTeamMutation.isPending ? "Confirmando..." : "Confirmar equipo"}
              </button>
              <button
                className="btn-secondary"
                onClick={() => navigate("/perfil")}
              >
                Administrar miembros
              </button>
            </div>
          </div>
        )}

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
            {billingQuery.data && (
              <div
                className={styles.stat}
                style={{ cursor: "pointer" }}
                onClick={() => navigate("/billing")}
                title="Ver mi plan"
              >
                <span className={styles.statValue}>
                  {billingQuery.data.processCount}/{billingQuery.data.processLimit}
                </span>
                <span className={styles.statLabel}>
                  Plan {billingQuery.data.planName}
                </span>
              </div>
            )}
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
              <button onClick={() => setShowEtiquetaManager(true)} className="btn-secondary">
                Etiquetas
              </button>
              <button onClick={() => setShowAddModal(true)} className="primary">
                + Agregar
              </button>
            </div>
          </div>

          {radicadosQuery.data && radicadosQuery.data.length > 0 && (
            <>
              <div className={styles.searchSortBar}>
                <input
                  type="text"
                  placeholder="Buscar por numero, alias, despacho..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className={styles.searchInput}
                />
                {(etiquetasQuery.data?.length ?? 0) > 0 && (
                  <EtiquetaFilter
                    etiquetas={etiquetasQuery.data || []}
                    value={filterEtiqueta}
                    onChange={setFilterEtiqueta}
                  />
                )}
                <div className={styles.sortGroup}>
                  <select
                    value={sortBy}
                    onChange={(e) => handleSetSortBy(e.target.value as "recent" | "alias" | "activo" | "numero")}
                    className={styles.sortSelect}
                  >
                    <option value="recent">Mas recientes</option>
                    {hasAlias && <option value="alias">Por alias</option>}
                    {hasMixedActivo && <option value="activo">Activos primero</option>}
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
              <FilterBar
                filters={filters}
                options={filterOptions}
                activeCount={filterCount}
                onToggle={toggleArrayFilter}
                onSetFilter={setFilter}
                onClearAll={clearFilters}
              />
            </>
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
          ) : (searchQuery || hasFilters) && filteredRadicados.length === 0 && (radicadosQuery.data?.length ?? 0) > 0 ? (
            <div className="empty-state">
              <div className="empty-state-icon">
                <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                  <circle cx="11" cy="11" r="8"/>
                  <line x1="21" y1="21" x2="16.65" y2="16.65"/>
                  <line x1="8" y1="11" x2="14" y2="11"/>
                </svg>
              </div>
              <p className="empty-state-text">
                {searchQuery ? `Sin resultados para "${searchQuery}"` : "Sin resultados con los filtros aplicados"}
              </p>
              <p className="empty-state-hint">
                {hasFilters
                  ? <button type="button" onClick={clearFilters} style={{ background: "none", border: "none", color: "var(--primary)", cursor: "pointer", textDecoration: "underline", fontSize: "inherit" }}>Limpiar filtros</button>
                  : "Intenta con otro termino de busqueda"
                }
              </p>
            </div>
          ) : (
            <>
              {hasFilters && filteredRadicados.length > 0 && filteredRadicados.length < (radicadosQuery.data?.length ?? 0) && (
                <p className={styles.filterResultsCount}>
                  Mostrando {filteredRadicados.length} de {radicadosQuery.data?.length} casos
                </p>
              )}
              <div
                key={JSON.stringify(filters)}
                className={viewMode === "grid" ? styles.radicadosGrid : styles.radicadosList}
              >
                {filteredRadicados.map((r: RadicadoDTO) => (
                  <div key={r.radicado} className={styles.cardWrapper}>
                    <RadicadoCard
                      radicado={r}
                      isSelected={false}
                      listMode={viewMode === "list"}
                      onSelect={() => navigate(`/radicado/${r.radicado}`)}
                      onDelete={() => setDeleteTarget(r)}
                      onEditAlias={(alias) => editAliasMutation.mutate({ radicado: r.radicado, alias })}
                      onToggleActivo={() => toggleMutation.mutate(r.radicado)}
                      onToggleEtiqueta={(etiquetaId, selected) => handleToggleEtiqueta(r, etiquetaId, selected)}
                      etiquetasResueltas={(r.etiquetas || [])
                        .map((id) => etiquetasMap.get(id))
                        .filter((e): e is EtiquetaDTO => e !== undefined)
                      }
                      todasEtiquetas={etiquetasQuery.data || []}
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
                  </div>
                ))}
              </div>
            </>
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
          onAdd={(radicado, alias, fuente, idProceso, meta) => addMutation.mutate({ radicado, alias, fuente, idProceso, meta })}
          onClose={() => setShowAddModal(false)}
          error={
            addMutation.error instanceof Error
              ? addMutation.error.message
              : null
          }
          loading={addMutation.isPending}
        />
      )}

      {showEtiquetaManager && (
        <EtiquetaManager
          etiquetas={etiquetasQuery.data || []}
          onClose={() => setShowEtiquetaManager(false)}
          onCreate={(nombre, color) => createEtiquetaMutation.mutate({ nombre, color })}
          onUpdate={(etiquetaId, nombre, color) => updateEtiquetaMutation.mutate({ etiquetaId, nombre, color })}
          onDelete={(etiquetaId) => deleteEtiquetaMutation.mutate(etiquetaId)}
          isCreating={createEtiquetaMutation.isPending}
          isUpdating={updateEtiquetaMutation.isPending}
          isDeleting={deleteEtiquetaMutation.isPending}
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
