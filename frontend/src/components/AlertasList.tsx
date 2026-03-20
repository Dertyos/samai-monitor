import type { AlertaDTO } from "../lib/api";
import { formatRadicado, formatDate, decodeHtml, timeAgo } from "../lib/utils";

interface Props {
  alertas: AlertaDTO[];
}

export default function AlertasList({ alertas }: Props) {
  if (alertas.length === 0) return null;

  // Group by radicado
  const grouped = new Map<string, AlertaDTO[]>();
  for (const a of alertas) {
    const list = grouped.get(a.radicado) || [];
    list.push(a);
    grouped.set(a.radicado, list);
  }

  return (
    <div className="alertas-list">
      {Array.from(grouped.entries()).map(([radicado, items]) => (
        <div key={radicado} className="alerta-group">
          <div className="alerta-group-header">
            <span className="alerta-group-radicado">
              {formatRadicado(radicado)}
            </span>
            <span className="alerta-group-count">
              {items.length} actuaci{items.length === 1 ? "ón" : "ones"}
            </span>
          </div>
          {items.map((a, i) => (
            <div key={`${a.radicado}-${a.orden}-${i}`} className="alerta-item">
              <div className="alerta-header">
                <span className="alerta-actuacion">{decodeHtml(a.nombreActuacion)}</span>
                <span className="alerta-orden">#{a.orden}</span>
              </div>
              <div className="alerta-meta">
                <span className="alerta-fecha">
                  {formatDate(a.fechaActuacion)}
                </span>
                {a.createdAt && (
                  <span className="alerta-time-ago">{timeAgo(a.createdAt)}</span>
                )}
              </div>
              {a.anotacion && <p className="alerta-anotacion">{decodeHtml(a.anotacion)}</p>}
            </div>
          ))}
        </div>
      ))}
    </div>
  );
}
