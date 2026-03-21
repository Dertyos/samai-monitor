import type { RadicadoDTO } from "../lib/api";
import styles from "./RadicadoCard.module.css";

interface Props {
  radicado: RadicadoDTO;
  isSelected: boolean;
  onSelect: () => void;
  onDelete: () => void;
  isDeleting: boolean;
}

export default function RadicadoCard({
  radicado,
  isSelected,
  onSelect,
  onDelete,
  isDeleting,
}: Props) {
  return (
    <div className={`${styles.card} ${isSelected ? styles.selected : ""}`}>
      <div className={styles.header} onClick={onSelect}>
        <span className={styles.radicadoFmt}>{radicado.radicadoFormato}</span>
        {radicado.alias && <span className={styles.alias}>{radicado.alias}</span>}
      </div>
      <div className={styles.body}>
        <span className={styles.meta}>
          Ultima actuacion: #{radicado.ultimoOrden}
        </span>
        <span className={radicado.activo ? styles.statusActive : styles.statusInactive}>
          {radicado.activo ? "Activo" : "Inactivo"}
        </span>
      </div>
      <div className={styles.actions}>
        <button onClick={onSelect} className="btn-secondary">
          {isSelected ? "Ocultar" : "Ver detalle"}
        </button>
        <button
          onClick={onDelete}
          className="btn-danger"
          disabled={isDeleting}
        >
          {isDeleting ? "..." : "Eliminar"}
        </button>
      </div>
    </div>
  );
}
