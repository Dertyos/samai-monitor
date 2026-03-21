import { useParams, useNavigate } from "react-router-dom";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { getDetalle, getDocumentoUrl, type ActuacionDTO } from "../lib/api";
import { formatDate, formatRadicado, decodeHtml } from "../lib/utils";
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
        <button
          onClick={() => queryClient.invalidateQueries({ queryKey: ["detalle", radicadoId] })}
          className="btn-secondary"
          disabled={query.isFetching}
        >
          {query.isFetching ? "Actualizando..." : "Actualizar"}
        </button>
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
          <section className={styles.section}>
            <h3>
              Historial de Actuaciones
              <span className={styles.count}> ({query.data.actuaciones.length})</span>
            </h3>

            {/* Mobile: cards */}
            <div className={styles.cards}>
              {query.data.actuaciones.map((a: ActuacionDTO) => (
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
                  {a.docHash && query.data && (
                    <a
                      href={getDocumentoUrl(query.data.corporacion, radicadoId, a.docHash)}
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
                  <th>#</th>
                  <th>Actuacion</th>
                  <th>Fecha</th>
                  <th>Estado</th>
                  <th>Decision</th>
                  <th>Anotacion</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {query.data.actuaciones.map((a: ActuacionDTO) => (
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
                      {a.docHash && query.data && (
                        <a
                          href={getDocumentoUrl(query.data.corporacion, radicadoId, a.docHash)}
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
        </>
      )}
    </div>
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
