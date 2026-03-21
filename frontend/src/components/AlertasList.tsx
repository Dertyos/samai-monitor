import { useMutation, useQueryClient } from "@tanstack/react-query";
import { type AlertaDTO, markAlertaRead } from "../lib/api";
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
 * Las alertas no leidas tienen estilo diferente y boton para marcar como leida.
 */
export default function AlertasList({ alertas }: Props) {
  const queryClient = useQueryClient();

  const markReadMutation = useMutation({
    mutationFn: markAlertaRead,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["alertas"] });
    },
  });

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
      {Array.from(grouped.entries()).map(([radicado, items]) => {
        const unreadCount = items.filter((a) => !a.leido).length;
        return (
          <div key={radicado} className={styles.group}>
            <div className={styles.groupHeader}>
              <span className={styles.groupRadicado}>
                {formatRadicado(radicado)}
              </span>
              <span className={styles.groupCount}>
                {items.length} actuaci{items.length === 1 ? "on" : "ones"}
                {unreadCount > 0 && ` (${unreadCount} nueva${unreadCount > 1 ? "s" : ""})`}
              </span>
            </div>
            {items.map((a, i) => (
              <div
                key={`${a.radicado}-${a.orden}-${i}`}
                className={`${styles.item} ${a.leido ? styles.itemRead : ""}`}
              >
                <div className={styles.itemHeader}>
                  <span className={styles.actuacion}>
                    {!a.leido && <span className={styles.unreadDot} />}
                    {decodeHtml(a.nombreActuacion)}
                  </span>
                  <div className={styles.itemActions}>
                    <span className={styles.orden}>#{a.orden}</span>
                    {!a.leido && (
                      <button
                        className={styles.markReadBtn}
                        onClick={() => markReadMutation.mutate(a.sk)}
                        disabled={markReadMutation.isPending}
                        title="Marcar como leida"
                      >
                        &#x2713;
                      </button>
                    )}
                  </div>
                </div>
                <div className={styles.itemMeta}>
                  <span>{formatDate(a.fechaActuacion)}</span>
                  {a.createdAt && (
                    <span className={styles.timeAgo}>{timeAgo(a.createdAt)}</span>
                  )}
                </div>
                {a.anotacion && <p className={styles.anotacion}>{decodeHtml(a.anotacion)}</p>}
              </div>
            ))}
          </div>
        );
      })}
    </div>
  );
}
