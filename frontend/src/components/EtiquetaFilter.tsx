import { useState, useRef, useEffect } from "react";
import type { EtiquetaDTO } from "../lib/api";
import styles from "./EtiquetaFilter.module.css";

interface Props {
  etiquetas: EtiquetaDTO[];
  value: string[];
  onChange: (ids: string[]) => void;
}

export default function EtiquetaFilter({ etiquetas, value, onChange }: Props) {
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

  const selectedEtiquetas = etiquetas.filter((e) => value.includes(e.etiquetaId));

  const handleToggle = (id: string) => {
    if (value.includes(id)) {
      onChange(value.filter((v) => v !== id));
    } else {
      onChange([...value, id]);
    }
  };

  return (
    <div className={`${styles.wrapper} ${open ? styles.wrapperOpen : ""}`} ref={ref}>
      <button
        className={`${styles.trigger} ${value.length > 0 ? styles.triggerActive : ""}`}
        onClick={() => setOpen(!open)}
        type="button"
      >
        {selectedEtiquetas.length > 0 ? (
          <>
            {selectedEtiquetas.map((etq) => (
              <span key={etq.etiquetaId} className={styles.triggerDot} style={{ backgroundColor: etq.color }} />
            ))}
            {selectedEtiquetas.length === 1 ? selectedEtiquetas[0].nombre : `${selectedEtiquetas.length} etiquetas`}
          </>
        ) : (
          "Todas las etiquetas"
        )}
        <span className={styles.triggerChevron}>&#x25BE;</span>
      </button>

      {open && (
        <div className={styles.dropdown}>
          {value.length > 0 && (
            <button
              className={styles.option}
              onClick={() => { onChange([]); setOpen(false); }}
            >
              Limpiar filtro
            </button>
          )}
          {etiquetas.map((etq) => {
            const isSelected = value.includes(etq.etiquetaId);
            return (
              <button
                key={etq.etiquetaId}
                className={`${styles.option} ${isSelected ? styles.optionSelected : ""}`}
                onClick={() => handleToggle(etq.etiquetaId)}
              >
                <span className={styles.optionDot} style={{ backgroundColor: etq.color }} />
                {etq.nombre}
                {isSelected && (
                  <svg style={{ width: 14, marginLeft: "auto", flexShrink: 0, color: "var(--primary)" }} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round">
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
