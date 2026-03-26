import { useState, useRef, useEffect } from "react";
import type { RadicadoDTO } from "../lib/api";
import styles from "./RadicadoCard.module.css";

interface Props {
  radicado: RadicadoDTO;
  isSelected: boolean;
  listMode?: boolean;
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
 * Acciones secundarias en menu dropdown (...) para ahorro de espacio.
 */
export default function RadicadoCard({
  radicado,
  isSelected,
  listMode = false,
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
  const [menuOpen, setMenuOpen] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);

  // Close menu on outside click
  useEffect(() => {
    if (!menuOpen) return;
    const handle = (e: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
        setMenuOpen(false);
      }
    };
    document.addEventListener("mousedown", handle);
    return () => document.removeEventListener("mousedown", handle);
  }, [menuOpen]);

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

  const cardClass = [
    styles.card,
    listMode ? styles.cardList : "",
    isSelected ? styles.selected : "",
    !radicado.activo ? styles.inactive : "",
  ].filter(Boolean).join(" ");

  const aliasNode = !editing && radicado.alias ? (
    <span
      className={styles.alias}
      onDoubleClick={(e) => { e.stopPropagation(); setEditing(true); }}
      title="Doble click para editar"
    >
      {radicado.alias}
    </span>
  ) : editing ? (
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
  ) : null;

  const [copied, setCopied] = useState(false);

  const handleCopyRadicado = (e: React.MouseEvent) => {
    e.stopPropagation();
    const digits = radicado.radicado.replace(/\D/g, "");
    navigator.clipboard.writeText(digits).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    });
  };

  const badgesNode = (
    <div className={styles.badges}>
      <span
        className={radicado.fuente === "rama_judicial" ? styles.badgeRj : styles.badgeSamai}
        title={radicado.fuente === "rama_judicial" ? "Fuente: Rama Judicial" : "Fuente: SAMAI"}
      >
        {radicado.fuente === "rama_judicial" ? "Rama J." : "Samai"}
      </span>
      <span className={radicado.activo ? styles.statusActive : styles.statusInactive}>
        {radicado.activo ? "Activo" : "Pausado"}
      </span>
    </div>
  );

  const menuNode = (
    <div className={styles.menuWrapper} ref={menuRef}>
      <button
        onClick={() => setMenuOpen(!menuOpen)}
        className={`btn-secondary ${styles.menuBtn}`}
        title="Mas acciones"
      >
        &#x22EF;
      </button>
      {menuOpen && (
        <div className={styles.menu}>
          <button
            onClick={() => { setEditing(true); setMenuOpen(false); }}
            disabled={isEditing}
          >
            {isEditing ? "..." : "Editar alias"}
          </button>
          <button
            onClick={() => { onToggleActivo(); setMenuOpen(false); }}
            disabled={isToggling}
          >
            {isToggling ? "..." : radicado.activo ? "Pausar monitoreo" : "Reactivar monitoreo"}
          </button>
          <button
            onClick={() => { setMenuOpen(false); onDelete(); }}
            className={styles.menuDanger}
            disabled={isDeleting}
          >
            {isDeleting ? "..." : "Eliminar"}
          </button>
        </div>
      )}
    </div>
  );

  if (listMode) {
    return (
      <div className={cardClass}>
        <div className={styles.listMain} onClick={onSelect}>
          <span
          className={styles.radicadoFmt}
          onClick={handleCopyRadicado}
          title={copied ? "¡Copiado!" : "Copiar número"}
          style={{ cursor: "copy" }}
        >
          {copied ? "¡Copiado!" : radicado.radicadoFormato}
        </span>
          {aliasNode}
        </div>
        <span className={`${styles.meta} ${styles.listMeta}`}>
          #{radicado.ultimoOrden}
        </span>
        {badgesNode}
        <div className={styles.actions}>
          <button onClick={onSelect} className="btn-secondary">
            Ver detalle
          </button>
          {menuNode}
        </div>
      </div>
    );
  }

  return (
    <div className={cardClass}>
      <div className={styles.header} onClick={onSelect}>
        <span
          className={styles.radicadoFmt}
          onClick={handleCopyRadicado}
          title={copied ? "¡Copiado!" : "Copiar número"}
          style={{ cursor: "copy" }}
        >
          {copied ? "¡Copiado!" : radicado.radicadoFormato}
        </span>
        {aliasNode}
      </div>
      <div className={styles.body}>
        <span className={styles.meta}>
          Ultima actuacion: #{radicado.ultimoOrden}
        </span>
        {badgesNode}
      </div>
      <div className={styles.actions}>
        <button onClick={onSelect} className="btn-secondary">
          Ver detalle
        </button>
        {menuNode}
      </div>
    </div>
  );
}
