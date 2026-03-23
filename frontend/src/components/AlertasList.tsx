import { useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import { type AlertaDTO, markAlertaRead } from "../lib/api";
import { formatRadicado, formatDate, decodeHtml, timeAgo } from "../lib/utils";
import styles from "./AlertasList.module.css";

interface Props {
  alertas: AlertaDTO[];
}

/**
 * AlertasList — muestra alertas no leidas agrupadas por radicado.
 *
 * Clic en una alerta la marca como leida (desaparece) y navega al detalle.
 * Cada grupo se puede colapsar/expandir clicando el header.
 */
export default function AlertasList({ alertas }: Props) {
  const queryClient = useQueryClient();
  const navigate = useNavigate();
  const [collapsed, setCollapsed] = useState<Set<string>>(new Set());

  const toggleGroup = (radicado: string) => {
    setCollapsed((prev) => {
      const next = new Set(prev);
      if (next.has(radicado)) next.delete(radicado);
      else next.add(radicado);
      return next;
    });
  };

  const markReadMutation = useMutation({
    mutationFn: markAlertaRead,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["alertas"] });
    },
  });

  const handleClick = (a: AlertaDTO) => {
    if (!a.leido) {
      markReadMutation.mutate(a.sk);
    }
    navigate(`/radicado/${a.radicado}`);
  };

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
        const isCollapsed = collapsed.has(radicado);
        return (
          <div key={radicado} className={styles.group}>
            <div
              className={styles.groupHeader}
              onClick={() => toggleGroup(radicado)}
            >
              <span className={styles.chevron}>{isCollapsed ? "\u25B8" : "\u25BE"}</span>
              <span className={styles.groupRadicado}>
                {formatRadicado(radicado)}
              </span>
              <span className={styles.groupCount}>
                {items.length} nueva{items.length !== 1 ? "s" : ""}
              </span>
              <a
                href={`https://samai.consejodeestado.gov.co/Vistas/Casos/list_procesos.aspx?guid=${formatRadicado(radicado)}`}
                target="_blank"
                rel="noopener noreferrer"
                className={styles.samaiLink}
                onClick={(e) => e.stopPropagation()}
              >
                Ver en SAMAI
              </a>
            </div>
            {!isCollapsed &&
              items.map((a, i) => (
                <div
                  key={`${a.radicado}-${a.orden}-${i}`}
                  className={styles.item}
                  onClick={() => handleClick(a)}
                >
                  <div className={styles.itemHeader}>
                    <span className={styles.actuacion}>
                      <span className={styles.unreadDot} />
                      {decodeHtml(a.nombreActuacion)}
                    </span>
                    <span className={styles.orden}>#{a.orden}</span>
                  </div>
                  <div className={styles.itemMeta}>
                    <span>Actuacion: {formatDate(a.fechaActuacion)}</span>
                    {a.createdAt && (
                      <span className={styles.notified}>
                        Notificado {timeAgo(a.createdAt)}
                      </span>
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
