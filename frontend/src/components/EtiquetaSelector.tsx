import { useState, useRef, useEffect } from "react";
import type { EtiquetaDTO } from "../lib/api";
import styles from "./EtiquetaSelector.module.css";

interface Props {
  etiquetas: EtiquetaDTO[];
  selectedIds: string[];
  onToggle: (etiquetaId: string, selected: boolean) => void;
}

export default function EtiquetaSelector({ etiquetas, selectedIds, onToggle }: Props) {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!open) return;
    const handle = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) {
        setOpen(false);
      }
    };
    document.addEventListener("mousedown", handle);
    return () => document.removeEventListener("mousedown", handle);
  }, [open]);

  if (etiquetas.length === 0) return null;

  return (
    <div className={styles.wrapper} ref={ref}>
      <button
        className={styles.trigger}
        onClick={(e) => { e.stopPropagation(); setOpen(!open); }}
        title="Asignar etiquetas"
      >
        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <path d="M20.59 13.41l-7.17 7.17a2 2 0 01-2.83 0L2 12V2h10l8.59 8.59a2 2 0 010 2.82z"/>
          <line x1="7" y1="7" x2="7.01" y2="7"/>
        </svg>
        Etiquetar
      </button>

      {open && (
        <div className={styles.dropdown}>
          {etiquetas.map((etq) => {
            const isSelected = selectedIds.includes(etq.etiquetaId);
            return (
              <button
                key={etq.etiquetaId}
                className={styles.option}
                onClick={(e) => {
                  e.stopPropagation();
                  onToggle(etq.etiquetaId, !isSelected);
                }}
              >
                <span className={styles.optionDot} style={{ backgroundColor: etq.color }} />
                <span>{etq.nombre}</span>
                {isSelected && (
                  <svg className={styles.optionCheck} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round">
                    <polyline points="20 6 9 17 4 12"/>
                  </svg>
                )}
              </button>
            );
          })}
        </div>
      )}
    </div>
  );
}
