import { useState, useRef, useEffect } from "react";
import type { EtiquetaDTO } from "../lib/api";
import styles from "./EtiquetaFilter.module.css";

interface Props {
  etiquetas: EtiquetaDTO[];
  value: string;
  onChange: (etiquetaId: string) => void;
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

  const selected = etiquetas.find((e) => e.etiquetaId === value);

  return (
    <div className={`${styles.wrapper} ${open ? styles.wrapperOpen : ""}`} ref={ref}>
      <button
        className={`${styles.trigger} ${value ? styles.triggerActive : ""}`}
        onClick={() => setOpen(!open)}
        type="button"
      >
        {selected ? (
          <>
            <span className={styles.triggerDot} style={{ backgroundColor: selected.color }} />
            {selected.nombre}
          </>
        ) : (
          "Todas las etiquetas"
        )}
        <span className={styles.triggerChevron}>&#x25BE;</span>
      </button>

      {open && (
        <div className={styles.dropdown}>
          <button
            className={`${styles.option} ${!value ? styles.optionSelected : ""}`}
            onClick={() => { onChange(""); setOpen(false); }}
          >
            Todas las etiquetas
          </button>
          {etiquetas.map((etq) => (
            <button
              key={etq.etiquetaId}
              className={`${styles.option} ${value === etq.etiquetaId ? styles.optionSelected : ""}`}
              onClick={() => { onChange(etq.etiquetaId); setOpen(false); }}
            >
              <span className={styles.optionDot} style={{ backgroundColor: etq.color }} />
              {etq.nombre}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
