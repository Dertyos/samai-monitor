import { useQuery } from "@tanstack/react-query";
import { getHistorial, type ActuacionDTO } from "../lib/api";
import { formatDate, decodeHtml } from "../lib/utils";

interface Props {
  radicado: string;
  radicadoFormato: string;
  onBack: () => void;
}

export default function Historial({ radicado, radicadoFormato, onBack }: Props) {
  const query = useQuery({
    queryKey: ["historial", radicado],
    queryFn: () => getHistorial(radicado),
  });

  return (
    <div className="historial-page">
      <div className="historial-header">
        <button onClick={onBack} className="btn-back">
          ← Volver
        </button>
        <h2>{radicadoFormato}</h2>
        {query.data && (
          <span className="count">{query.data.length} actuaciones</span>
        )}
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
        <div className="actuaciones-container">
          {/* Mobile: cards */}
          <div className="actuaciones-cards">
            {query.data.map((a: ActuacionDTO) => (
              <div key={a.orden} className="actuacion-card">
                <div className="actuacion-card-header">
                  <span className="actuacion-card-orden">#{a.orden}</span>
                  <span className="actuacion-card-fecha">
                    {formatDate(a.fecha)}
                  </span>
                </div>
                <div className="actuacion-card-nombre">{decodeHtml(a.nombre)}</div>
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
                <th>Actuación</th>
                <th>Fecha</th>
                <th>Anotación</th>
              </tr>
            </thead>
            <tbody>
              {query.data.map((a: ActuacionDTO) => (
                <tr key={a.orden}>
                  <td>{a.orden}</td>
                  <td>{decodeHtml(a.nombre)}</td>
                  <td>{formatDate(a.fecha)}</td>
                  <td className="anotacion">{decodeHtml(a.anotacion)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
