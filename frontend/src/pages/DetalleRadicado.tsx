import { useState, useMemo, useRef, useEffect } from "react";
import { useParams, useNavigate, Link } from "react-router-dom";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { getRadicados, getDetalle, getDocumentoUrl, type ActuacionDTO, type RadicadoDTO } from "../lib/api";
import { formatDate, formatRadicado, decodeHtml } from "../lib/utils";
import { useToast } from "../hooks/useToast";
import { useTheme } from "../hooks/useTheme";
import AppLogo from "../components/AppLogo";

function exportToCsv(actuaciones: ActuacionDTO[], radicado: string): void {
  const header = "Orden,Actuacion,Fecha,Estado,Decision,Anotacion";
  const escape = (s: string) => `"${decodeHtml(s).replace(/"/g, '""')}"`;
  const rows = actuaciones.map((a) =>
    [a.orden, escape(a.nombre), formatDate(a.fecha), a.estado, escape(a.decision ?? ""), escape(a.anotacion)].join(","),
  );
  const csv = [header, ...rows].join("\n");
  const blob = new Blob(["\uFEFF" + csv], { type: "text/csv;charset=utf-8;" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `actuaciones_${radicado}.csv`;
  a.click();
  URL.revokeObjectURL(url);
}
import styles from "./DetalleRadicado.module.css";

/**
 * DetalleRadicado — vista completa de un proceso judicial.
 *
 * Lee el radicado de la URL via useParams (ruta: /radicado/:radicadoId).
 * Consulta la API de detalle que a su vez consulta SAMAI.
 *
 * Secciones:
 * 1. Datos del proceso (despacho, ponente, tipo, clase, fecha)
 * 2. Partes procesales (demandante, demandado, etc.)
 * 3. Historial de actuaciones (tabla desktop, cards mobile)
 *
 * Navegación:
 * - Botones ← Anterior / Siguiente → en el header
 * - Sidebar derecho con lista completa + buscador (desktop ≥1024px)
 */
export default function DetalleRadicado() {
  const { radicadoId } = useParams<{ radicadoId: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const toast = useToast();
  const { theme, toggle: toggleTheme } = useTheme();
  const [actuacionSearch, setActuacionSearch] = useState("");
  const [copied, setCopied] = useState(false);
  const [sidebarSearch, setSidebarSearch] = useState("");
  const [sidebarOpen, setSidebarOpen] = useState<boolean>(
    () => localStorage.getItem("detalleSidebarOpen") !== "false"
  );
  const currentItemRef = useRef<HTMLButtonElement>(null);

  const handleToggleSidebar = () => {
    const next = !sidebarOpen;
    localStorage.setItem("detalleSidebarOpen", String(next));
    setSidebarOpen(next);
  };

  const handleCopyRadicado = () => {
    navigator.clipboard.writeText(radicadoId!).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    });
  };

  const query = useQuery({
    queryKey: ["detalle", radicadoId],
    queryFn: () => getDetalle(radicadoId!),
    enabled: !!radicadoId,
    staleTime: 5 * 60 * 1000, // 5 min — datos de SAMAI no cambian tan rapido
  });

  // Radicados para navegación — usa caché del dashboard, no genera nueva petición
  const radicadosQuery = useQuery({
    queryKey: ["radicados"],
    queryFn: getRadicados,
    staleTime: 2 * 60 * 1000,
  });

  // Mismo orden que el dashboard (persiste en localStorage via handleSetSortBy)
  const sortedRadicados = useMemo(() => {
    if (!radicadosQuery.data) return [];
    const sortPref = (localStorage.getItem("sortBy") as "recent" | "alias" | "activo" | "numero") ?? "recent";
    const sortDir = (localStorage.getItem("sortDir") as "asc" | "desc") ?? "desc";
    return [...radicadosQuery.data].sort((a: RadicadoDTO, b: RadicadoDTO) => {
      let cmp = 0;
      if (sortPref === "alias") cmp = a.alias.localeCompare(b.alias);
      else if (sortPref === "activo") cmp = (b.activo ? 1 : 0) - (a.activo ? 1 : 0);
      else if (sortPref === "numero") cmp = a.radicado.localeCompare(b.radicado);
      else if (sortPref === "recent") {
        const fa = a.fechaUltimaActuacion || a.createdAt || "";
        const fb = b.fechaUltimaActuacion || b.createdAt || "";
        cmp = fa.localeCompare(fb);
      }
      return sortDir === "asc" ? cmp : -cmp;
    });
  }, [radicadosQuery.data]);

  const currentIndex = sortedRadicados.findIndex((r) => r.radicado === radicadoId);
  const prevRadicado = currentIndex > 0 ? sortedRadicados[currentIndex - 1] : null;
  const nextRadicado = currentIndex < sortedRadicados.length - 1 ? sortedRadicados[currentIndex + 1] : null;

  // Lista filtrada que se muestra en el sidebar (no afecta la navegación prev/next)
  const sidebarFiltered = useMemo(() => {
    if (!sidebarSearch) return sortedRadicados;
    const q = sidebarSearch.toLowerCase();
    return sortedRadicados.filter(
      (r) =>
        r.alias.toLowerCase().includes(q) ||
        r.radicadoFormato.toLowerCase().includes(q) ||
        r.radicado.includes(q),
    );
  }, [sortedRadicados, sidebarSearch]);

  // Auto-scroll al caso actual en el sidebar cuando cambia el radicado
  useEffect(() => {
    currentItemRef.current?.scrollIntoView({ block: "nearest", behavior: "smooth" });
  }, [radicadoId]);

  if (!radicadoId) {
    return <p className="error">Radicado no especificado</p>;
  }

  const radicadoFormato = formatRadicado(radicadoId);
  const showNav = sortedRadicados.length > 1;

  return (
    <div className={styles.pageWrapper}>
      <header className={styles.appHeader}>
        <Link to="/dashboard" className={styles.appHeaderBrand}>
          <AppLogo size={26} />
          Alertas Judiciales
        </Link>
        <button
          onClick={toggleTheme}
          className="theme-toggle"
          aria-label={theme === "light" ? "Cambiar a modo oscuro" : "Cambiar a modo claro"}
          title={theme === "light" ? "Cambiar a modo oscuro" : "Cambiar a modo claro"}
        >
          {theme === "light" ? "\u{1F319}" : "\u{2600}\u{FE0F}"}
        </button>
      </header>

      <div className={styles.pageBody}>
        <div className={styles.page}>
          <div className={styles.header}>
            {/* Fila de navegación: Volver + prev/next */}
            <div className={styles.headerNav}>
              <button onClick={() => navigate("/dashboard")} className="btn-back">
                &larr; Volver
              </button>
              {showNav && (
                <div className={styles.caseNavButtons}>
                  <button
                    onClick={() => prevRadicado && navigate(`/radicado/${prevRadicado.radicado}`)}
                    className="btn-secondary"
                    disabled={!prevRadicado}
                    title={prevRadicado ? (prevRadicado.alias || prevRadicado.radicadoFormato) : undefined}
                  >
                    &larr; Anterior
                  </button>
                  <span className={styles.caseNavPosition}>
                    {currentIndex >= 0 ? `${currentIndex + 1}/${sortedRadicados.length}` : `?/${sortedRadicados.length}`}
                  </span>
                  <button
                    onClick={() => nextRadicado && navigate(`/radicado/${nextRadicado.radicado}`)}
                    className="btn-secondary"
                    disabled={!nextRadicado}
                    title={nextRadicado ? (nextRadicado.alias || nextRadicado.radicadoFormato) : undefined}
                  >
                    Siguiente &rarr;
                  </button>
                </div>
              )}
            </div>

            <h2
              onClick={handleCopyRadicado}
              title={copied ? "¡Copiado!" : "Copiar número"}
              style={{ cursor: "copy" }}
            >
              {copied ? "¡Copiado!" : radicadoFormato}
            </h2>
            <div className={styles.headerActions}>
              {query.data && (
                <button
                  onClick={() => exportToCsv(query.data.actuaciones, radicadoId)}
                  className="btn-secondary"
                >
                  Exportar CSV
                </button>
              )}
              <button
                onClick={() => queryClient.invalidateQueries({ queryKey: ["detalle", radicadoId] })}
                className="btn-secondary"
                disabled={query.isFetching}
              >
                {query.isFetching ? "Actualizando..." : "Actualizar"}
              </button>
              <div className={styles.samaiLinkGroup}>
                {query.data?.fuente === "rama_judicial" ? (
                  <a
                    href={`https://consultaprocesos.ramajudicial.gov.co/Procesos/NumeroRadicacion`}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="btn-secondary"
                    title="Abrir en Consulta de Procesos (Rama Judicial)"
                  >
                    Ver en Rama Judicial
                  </a>
                ) : (
                  <>
                    <a
                      href={query.data ? `https://samai.consejodeestado.gov.co/Vistas/Casos/list_procesos.aspx?guid=${radicadoFormato}${query.data.corporacion}` : `https://samai.consejodeestado.gov.co/Vistas/Casos/list_procesos.aspx?guid=${radicadoFormato}`}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="btn-secondary"
                      title="Abrir en SAMAI. Si tienes error de corporación, cópialo y ábrelo en Incógnito."
                    >
                      Ver en SAMAI
                    </a>
                    <button
                      onClick={() => {
                        const url = query.data ? `https://samai.consejodeestado.gov.co/Vistas/Casos/list_procesos.aspx?guid=${radicadoFormato}${query.data.corporacion}` : `https://samai.consejodeestado.gov.co/Vistas/Casos/list_procesos.aspx?guid=${radicadoFormato}`;
                        navigator.clipboard.writeText(url);
                        toast.info("Enlace copiado. Si SAMAI da error de corporacion, pegalo en Incognito.");
                      }}
                      className="btn-secondary"
                      title="Copiar enlace para abrir en Incognito"
                      aria-label="Copiar enlace de SAMAI"
                      style={{ padding: "0.25rem 0.5rem" }}
                    >
                      📋
                    </button>
                  </>
                )}
              </div>
            </div>
          </div>

          {query.isLoading && (
            <div className="loading-container">
              <div className="spinner" />
              <p>Consultando datos del proceso...</p>
            </div>
          )}
          {query.error && (
            <p className="error">
              Error: {query.error instanceof Error ? query.error.message : "Error"}
            </p>
          )}

          {query.data && (
            <>
              {/* Seccion 1: Datos del proceso */}
              <section className={styles.section}>
                <h3>Datos del Proceso</h3>
                <div className={styles.infoGrid}>
                  <InfoItem label="Despacho" value={query.data.proceso.despacho} />
                  <InfoItem label="Ponente" value={query.data.proceso.ponente} />
                  <InfoItem label="Tipo de Proceso" value={query.data.proceso.tipoProceso} />
                  <InfoItem label="Clase" value={query.data.proceso.claseActuacion} />
                  <InfoItem
                    label="Fecha Ult. Actuacion"
                    value={formatDate(query.data.proceso.fechaUltimaActuacion)}
                  />
                </div>
              </section>

              {/* Seccion 2: Partes procesales */}
              <section className={styles.section}>
                <h3>Partes Procesales</h3>
                {query.data.partes.length === 0 ? (
                  <p className={styles.emptyText}>Sin partes registradas</p>
                ) : (
                  <div className={styles.partesList}>
                    {query.data.partes.map((p, i) => (
                      <div key={i} className={styles.parteItem}>
                        <span className={styles.parteTipo}>{p.tipo}</span>
                        <span className={styles.parteNombre}>{decodeHtml(p.nombre)}</span>
                      </div>
                    ))}
                  </div>
                )}
              </section>

              {/* Seccion 3: Historial de actuaciones */}
              <ActuacionesSection
                actuaciones={query.data.actuaciones}
                corporacion={query.data.corporacion ?? ""}
                radicadoId={radicadoId}
                search={actuacionSearch}
                onSearchChange={setActuacionSearch}
              />
            </>
          )}
        </div>

        {/* Sidebar de navegación entre casos (solo desktop ≥1024px) */}
        {showNav && (
          <aside className={`${styles.caseSidebar}${!sidebarOpen ? ` ${styles.caseSidebarCollapsed}` : ""}`}>
            <div className={styles.sidebarTitle}>
              {sidebarOpen && (
                <>
                  Mis casos{" "}
                  <span className={styles.sidebarCount}>{sortedRadicados.length}</span>
                </>
              )}
              <button
                onClick={handleToggleSidebar}
                className={styles.sidebarToggle}
                title={sidebarOpen ? "Colapsar" : "Expandir panel de casos"}
                aria-label={sidebarOpen ? "Colapsar panel de casos" : "Expandir panel de casos"}
              >
                {sidebarOpen ? "‹" : "›"}
              </button>
            </div>
            {sidebarOpen && (
              <>
                <div className={styles.sidebarSearchWrap}>
                  <input
                    type="search"
                    placeholder="Buscar caso..."
                    value={sidebarSearch}
                    onChange={(e) => setSidebarSearch(e.target.value)}
                    className={styles.sidebarSearch}
                    aria-label="Filtrar casos en sidebar"
                  />
                </div>
                {sidebarSearch && (
                  <div className={styles.sidebarFilterInfo}>
                    {sidebarFiltered.length} de {sortedRadicados.length}
                  </div>
                )}
                <nav className={styles.sidebarList}>
                  {sidebarFiltered.map((r) => (
                    <button
                      key={r.radicado}
                      ref={r.radicado === radicadoId ? currentItemRef : undefined}
                      className={`${styles.caseNavItem}${r.radicado === radicadoId ? ` ${styles.caseNavItemCurrent}` : ""}`}
                      onClick={() => navigate(`/radicado/${r.radicado}`)}
                      title={r.radicadoFormato}
                    >
                      <span className={styles.caseNavItemText}>
                        <span className={styles.caseNavItemAlias}>
                          {r.alias || r.radicadoFormato}
                        </span>
                        {r.alias && (
                          <span className={styles.caseNavItemNum}>{r.radicadoFormato}</span>
                        )}
                      </span>
                      {!r.activo && <span className={styles.caseNavItemPaused}>⏸</span>}
                    </button>
                  ))}
                  {sidebarSearch && sidebarFiltered.length === 0 && (
                    <p className={styles.sidebarEmpty}>Sin resultados</p>
                  )}
                </nav>
              </>
            )}
          </aside>
        )}
      </div>
    </div>
  );
}

type SortKey = "orden" | "nombre" | "fecha" | "estado" | "decision" | "anotacion";
type SortDir = "asc" | "desc";

function ActuacionesSection({
  actuaciones,
  corporacion,
  radicadoId,
  search,
  onSearchChange,
}: {
  actuaciones: ActuacionDTO[];
  corporacion: string;
  radicadoId: string;
  search: string;
  onSearchChange: (v: string) => void;
}) {
  const [sortKey, setSortKey] = useState<SortKey>("orden");
  const [sortDir, setSortDir] = useState<SortDir>("desc");

  const handleSort = (key: SortKey) => {
    if (sortKey === key) {
      setSortDir((d) => (d === "asc" ? "desc" : "asc"));
    } else {
      setSortKey(key);
      setSortDir(key === "orden" ? "desc" : "asc");
    }
  };

  const filtered = useMemo(() => {
    let list = actuaciones;
    if (search) {
      const q = search.toLowerCase();
      list = list.filter(
        (a) =>
          decodeHtml(a.nombre).toLowerCase().includes(q) ||
          decodeHtml(a.anotacion).toLowerCase().includes(q) ||
          (a.decision && decodeHtml(a.decision).toLowerCase().includes(q)) ||
          (a.estado && a.estado.toLowerCase().includes(q)) ||
          String(a.orden).includes(q),
      );
    }
    const sorted = [...list].sort((a, b) => {
      let cmp = 0;
      switch (sortKey) {
        case "orden":
          cmp = a.orden - b.orden;
          break;
        case "nombre":
          cmp = decodeHtml(a.nombre).localeCompare(decodeHtml(b.nombre));
          break;
        case "fecha":
          cmp = (a.fecha || "").localeCompare(b.fecha || "");
          break;
        case "estado":
          cmp = (a.estado || "").localeCompare(b.estado || "");
          break;
        case "decision":
          cmp = (a.decision || "").localeCompare(b.decision || "");
          break;
        case "anotacion":
          cmp = decodeHtml(a.anotacion).localeCompare(decodeHtml(b.anotacion));
          break;
      }
      return sortDir === "asc" ? cmp : -cmp;
    });
    return sorted;
  }, [actuaciones, search, sortKey, sortDir]);

  return (
          <section className={styles.section}>
            <h3>
              Historial de Actuaciones
              <span className={styles.count}>
                {search
                  ? ` (${filtered.length} de ${actuaciones.length})`
                  : ` (${actuaciones.length})`}
              </span>
            </h3>

            {actuaciones.length > 5 && (
              <label className={styles.actuacionSearchLabel}>
                <span className="sr-only">Filtrar actuaciones</span>
                <input
                  type="search"
                  placeholder="Filtrar actuaciones..."
                  value={search}
                  onChange={(e) => onSearchChange(e.target.value)}
                  className={styles.actuacionSearch}
                  aria-label="Filtrar actuaciones"
                />
              </label>
            )}

            {/* Mobile: cards */}
            <div className={styles.cards}>
              {filtered.map((a: ActuacionDTO) => (
                <div key={a.orden} className={styles.card}>
                  <div className={styles.cardHeader}>
                    <span className={styles.cardOrden}>#{a.orden}</span>
                    <span className={styles.cardFecha}>{formatDate(a.fecha)}</span>
                  </div>
                  <div className={styles.cardNombre}>{decodeHtml(a.nombre)}</div>
                  {a.estado && (
                    <span className={styles.estadoBadge}>{a.estado}</span>
                  )}
                  {a.decision && (
                    <p className={styles.decisionText}>{decodeHtml(a.decision)}</p>
                  )}
                  {a.anotacion && (
                    <p className={styles.cardAnotacion}>{decodeHtml(a.anotacion)}</p>
                  )}
                  {a.docHash && (
                    <a
                      href={getDocumentoUrl(corporacion, radicadoId, a.docHash)}
                      target="_blank"
                      rel="noopener noreferrer"
                      className={styles.downloadBtn}
                    >
                      Descargar documento
                    </a>
                  )}
                </div>
              ))}
            </div>

            {/* Desktop: table */}
            <table className={styles.table}>
              <thead>
                <tr>
                  {([["orden", "#"], ["nombre", "Actuacion"], ["fecha", "Fecha"], ["estado", "Estado"], ["decision", "Decision"], ["anotacion", "Anotacion"]] as [SortKey, string][]).map(([key, label]) => (
                    <th
                      key={key}
                      onClick={() => handleSort(key)}
                      className={styles.sortable}
                    >
                      {label} {sortKey === key ? (sortDir === "asc" ? "▲" : "▼") : ""}
                    </th>
                  ))}
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {filtered.map((a: ActuacionDTO) => (
                  <tr key={a.orden}>
                    <td>{a.orden}</td>
                    <td>{decodeHtml(a.nombre)}</td>
                    <td>{formatDate(a.fecha)}</td>
                    <td>
                      {a.estado && (
                        <span className={styles.estadoBadge}>{a.estado}</span>
                      )}
                    </td>
                    <td className={styles.decisionCell}>{a.decision ? decodeHtml(a.decision) : ""}</td>
                    <td className={styles.anotacionCell}>{decodeHtml(a.anotacion)}</td>
                    <td>
                      {a.docHash && (
                        <a
                          href={getDocumentoUrl(corporacion, radicadoId, a.docHash)}
                          target="_blank"
                          rel="noopener noreferrer"
                          className={styles.downloadLink}
                        >
                          PDF
                        </a>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </section>
  );
}

/**
 * InfoItem — componente reutilizable para mostrar un campo label/value.
 *
 * Usado en la seccion "Datos del Proceso" de DetalleRadicado.
 */
function InfoItem({ label, value }: { label: string; value: string }) {
  return (
    <div className={styles.infoItem}>
      <span className={styles.infoLabel}>{label}</span>
      <span className={styles.infoValue}>{value || "\u2014"}</span>
    </div>
  );
}
