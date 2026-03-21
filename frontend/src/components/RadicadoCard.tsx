import { useState } from "react";
import type { RadicadoDTO } from "../lib/api";
import styles from "./RadicadoCard.module.css";

interface Props {
  radicado: RadicadoDTO;
  isSelected: boolean;
  onSelect: () => void;
  onDelete: () => void;
  onEditAlias: (newAlias: string) => void;
  onToggleActivo: () => void;
  isDeleting: boolean;
  isEditing: boolean;
  isToggling: boolean;
}

/**
 * RadicadoCard — tarjeta de radicado con acciones.
 *
 * Reutilizable: recibe RadicadoDTO y callbacks para acciones.
 * Soporta inline editing del alias (doble click o boton editar).
 */
export default function RadicadoCard({
  radicado,
  isSelected,
  onSelect,
  onDelete,
  onEditAlias,
  onToggleActivo,
  isDeleting,
  isEditing,
  isToggling,
}: Props) {
  const [editing, setEditing] = useState(false);
  const [aliasInput, setAliasInput] = useState(radicado.alias);

  const handleSaveAlias = () => {
    if (aliasInput.trim() !== radicado.alias) {
      onEditAlias(aliasInput.trim());
    }
    setEditing(false);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter") handleSaveAlias();
    if (e.key === "Escape") {
      setAliasInput(radicado.alias);
      setEditing(false);
    }
  };

  return (
    <div className={`${styles.card} ${isSelected ? styles.selected : ""}`}>
      <div className={styles.header} onClick={onSelect}>
        <span className={styles.radicadoFmt}>{radicado.radicadoFormato}</span>
        {!editing && radicado.alias && (
          <span
            className={styles.alias}
            onDoubleClick={(e) => { e.stopPropagation(); setEditing(true); }}
            title="Doble click para editar"
          >
            {radicado.alias}
          </span>
        )}
        {editing && (
          <input
            type="text"
            value={aliasInput}
            onChange={(e) => setAliasInput(e.target.value)}
            onBlur={handleSaveAlias}
            onKeyDown={handleKeyDown}
            onClick={(e) => e.stopPropagation()}
            className={styles.aliasInput}
            autoFocus
            placeholder="Alias"
          />
        )}
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
          Ver detalle
        </button>
        <button
          onClick={() => setEditing(true)}
          className="btn-secondary"
          disabled={isEditing}
        >
          {isEditing ? "..." : "Editar alias"}
        </button>
        <button
          onClick={onToggleActivo}
          className="btn-secondary"
          disabled={isToggling}
        >
          {isToggling ? "..." : radicado.activo ? "Pausar" : "Reactivar"}
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
