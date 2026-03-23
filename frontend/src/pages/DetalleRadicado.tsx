import { useState, useMemo } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { getDetalle, getDocumentoUrl, type ActuacionDTO } from "../lib/api";
import { formatDate, formatRadicado, decodeHtml } from "../lib/utils";

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
 */
export default function DetalleRadicado() {
  const { radicadoId } = useParams<{ radicadoId: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [actuacionSearch, setActuacionSearch] = useState("");

  const query = useQuery({
    queryKey: ["detalle", radicadoId],
    queryFn: () => getDetalle(radicadoId!),
    enabled: !!radicadoId,
    staleTime: 5 * 60 * 1000, // 5 min — datos de SAMAI no cambian tan rapido
  });

  if (!radicadoId) {
    return <p className="error">Radicado no especificado</p>;
  }

  const radicadoFormato = formatRadicado(radicadoId);

  return (
    <div className={styles.page}>
      <div className={styles.header}>
        <button onClick={() => navigate("/dashboard")} className="btn-back">
          &larr; Volver
        </button>
        <h2>{radicadoFormato}</h2>
        <div className={styles.headerActions}>
          <a
            href={`https://samai.consejodeestado.gov.co/Vistas/Casos/list_procesos.aspx?guid=${radicadoFormato}`}
            target="_blank"
            rel="noopener noreferrer"
            className="btn-secondary"
          >
            Ver en SAMAI
          </a>
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
        </div>
      </div>

      {query.isLoading && (
        <div className="loading-container">
          <div className="spinner" />
          <p>Consultando SAMAI...</p>
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
            corporacion={query.data.corporacion}
            radicadoId={radicadoId}
            search={actuacionSearch}
            onSearchChange={setActuacionSearch}
          />
        </>
      )}
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
              <input
                type="text"
                placeholder="Filtrar actuaciones..."
                value={search}
                onChange={(e) => onSearchChange(e.target.value)}
                className={styles.actuacionSearch}
              />
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
