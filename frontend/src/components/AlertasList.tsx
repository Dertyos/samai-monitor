import type { AlertaDTO } from "../lib/api";
import { formatRadicado, formatDate, decodeHtml, timeAgo } from "../lib/utils";
import styles from "./AlertasList.module.css";

interface Props {
  alertas: AlertaDTO[];
}

/**
 * AlertasList — muestra alertas agrupadas por radicado.
 *
 * Reutilizable: recibe un array de AlertaDTO y las agrupa internamente.
 * Cada grupo muestra el radicado formateado y la cantidad de actuaciones.
 */
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
    <div className={styles.list}>
      {Array.from(grouped.entries()).map(([radicado, items]) => (
        <div key={radicado} className={styles.group}>
          <div className={styles.groupHeader}>
            <span className={styles.groupRadicado}>
              {formatRadicado(radicado)}
            </span>
            <span className={styles.groupCount}>
              {items.length} actuaci{items.length === 1 ? "on" : "ones"}
            </span>
          </div>
          {items.map((a, i) => (
            <div key={`${a.radicado}-${a.orden}-${i}`} className={styles.item}>
              <div className={styles.itemHeader}>
                <span className={styles.actuacion}>{decodeHtml(a.nombreActuacion)}</span>
                <span className={styles.orden}>#{a.orden}</span>
              </div>
              <div className={styles.itemMeta}>
                <span>
                  {formatDate(a.fechaActuacion)}
                </span>
                {a.createdAt && (
                  <span className={styles.timeAgo}>{timeAgo(a.createdAt)}</span>
                )}
              </div>
              {a.anotacion && <p className={styles.anotacion}>{decodeHtml(a.anotacion)}</p>}
            </div>
          ))}
        </div>
      ))}
    </div>
  );
}
