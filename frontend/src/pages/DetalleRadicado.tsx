import { useQuery } from "@tanstack/react-query";
import { getDetalle, type ActuacionDTO } from "../lib/api";
import { formatDate, decodeHtml } from "../lib/utils";

interface Props {
  radicado: string;
  radicadoFormato: string;
  alias: string;
  onBack: () => void;
}

export default function DetalleRadicado({ radicado, radicadoFormato, alias, onBack }: Props) {
  const query = useQuery({
    queryKey: ["detalle", radicado],
    queryFn: () => getDetalle(radicado),
  });

  return (
    <div className="detalle-page">
      <div className="detalle-header">
        <button onClick={onBack} className="btn-back">
          &larr; Volver
        </button>
        <h2>{radicadoFormato}</h2>
        {alias && <span className="detalle-alias">{alias}</span>}
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
          <section className="detalle-section">
            <h3>Datos del Proceso</h3>
            <div className="detalle-grid">
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
          <section className="detalle-section">
            <h3>Partes Procesales</h3>
            {query.data.partes.length === 0 ? (
              <p className="detalle-empty">Sin partes registradas</p>
            ) : (
              <div className="partes-list">
                {query.data.partes.map((p, i) => (
                  <div key={i} className="parte-item">
                    <span className="parte-tipo">{p.tipo}</span>
                    <span className="parte-nombre">{decodeHtml(p.nombre)}</span>
                  </div>
                ))}
              </div>
            )}
          </section>

          {/* Seccion 3: Historial de actuaciones */}
          <section className="detalle-section">
            <h3>
              Historial de Actuaciones
              <span className="count"> ({query.data.actuaciones.length})</span>
            </h3>

            {/* Mobile: cards */}
            <div className="actuaciones-cards">
              {query.data.actuaciones.map((a: ActuacionDTO) => (
                <div key={a.orden} className="actuacion-card">
                  <div className="actuacion-card-header">
                    <span className="actuacion-card-orden">#{a.orden}</span>
                    <span className="actuacion-card-fecha">{formatDate(a.fecha)}</span>
                  </div>
                  <div className="actuacion-card-nombre">{decodeHtml(a.nombre)}</div>
                  {a.estado && (
                    <span className="actuacion-estado-badge">{a.estado}</span>
                  )}
                  {a.decision && (
                    <p className="actuacion-decision">{decodeHtml(a.decision)}</p>
                  )}
                  {a.anotacion && (
                    <p className="actuacion-card-anotacion">{decodeHtml(a.anotacion)}</p>
                  )}
                </div>
              ))}
            </div>

            {/* Desktop: table */}
            <table className="actuaciones-table">
              <thead>
                <tr>
                  <th>#</th>
                  <th>Actuacion</th>
                  <th>Fecha</th>
                  <th>Estado</th>
                  <th>Decision</th>
                  <th>Anotacion</th>
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
                        <span className="actuacion-estado-badge">{a.estado}</span>
                      )}
                    </td>
                    <td className="decision">{a.decision ? decodeHtml(a.decision) : ""}</td>
                    <td className="anotacion">{decodeHtml(a.anotacion)}</td>
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

function InfoItem({ label, value }: { label: string; value: string }) {
  return (
    <div className="info-item">
      <span className="info-label">{label}</span>
      <span className="info-value">{value || "—"}</span>
    </div>
  );
}
