import { useState, useRef, useEffect } from "react";
import type { RadicadoDTO, EtiquetaDTO } from "../lib/api";
import EtiquetaSelector from "./EtiquetaSelector";
import styles from "./RadicadoCard.module.css";

interface EtiquetaResuelta {
  etiquetaId: string;
  nombre: string;
  color: string;
}

interface Props {
  radicado: RadicadoDTO;
  isSelected: boolean;
  listMode?: boolean;
  onSelect: () => void;
  onDelete: () => void;
  onEditAlias: (newAlias: string) => void;
  onToggleActivo: () => void;
  onToggleEtiqueta?: (etiquetaId: string, selected: boolean) => void;
  etiquetasResueltas?: EtiquetaResuelta[];
  todasEtiquetas?: EtiquetaDTO[];
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
/**
 * Calcula un color de texto legible (blanco o negro) según el fondo.
 */
function textColorForBg(hex: string): string {
  const r = parseInt(hex.slice(1, 3), 16);
  const g = parseInt(hex.slice(3, 5), 16);
  const b = parseInt(hex.slice(5, 7), 16);
  // Luminancia relativa simplificada
  const lum = (0.299 * r + 0.587 * g + 0.114 * b) / 255;
  return lum > 0.55 ? "#000000" : "#ffffff";
}

export default function RadicadoCard({
  radicado,
  isSelected,
  listMode = false,
  onSelect,
  onDelete,
  onEditAlias,
  onToggleActivo,
  onToggleEtiqueta,
  etiquetasResueltas = [],
  todasEtiquetas = [],
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

  const etiquetasNode = etiquetasResueltas.length > 0 ? (
    <div className={styles.etiquetas}>
      {etiquetasResueltas.map((etq) => (
        <span
          key={etq.etiquetaId}
          className={styles.etiquetaPill}
          style={{
            backgroundColor: etq.color,
            color: textColorForBg(etq.color),
          }}
        >
          {etq.nombre}
        </span>
      ))}
    </div>
  ) : null;

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
      {onToggleEtiqueta && todasEtiquetas.length > 0 && (
        <EtiquetaSelector
          etiquetas={todasEtiquetas}
          selectedIds={radicado.etiquetas || []}
          onToggle={onToggleEtiqueta}
        />
      )}
    </div>
  );

  const menuNode = (
    <div className={styles.menuWrapper} ref={menuRef}>
      <button
        onClick={() => setMenuOpen(!menuOpen)}
        className={`btn-secondary ${styles.menuBtn}`}
        title="Mas acciones"
        aria-label="Mas acciones"
        aria-expanded={menuOpen}
        aria-haspopup="menu"
      >
        &#x22EF;
      </button>
      {menuOpen && (
        <div className={styles.menu} role="menu">
          <button
            role="menuitem"
            onClick={() => { setEditing(true); setMenuOpen(false); }}
            disabled={isEditing}
          >
            {isEditing ? "Guardando..." : "Editar alias"}
          </button>
          <button
            role="menuitem"
            onClick={() => { onToggleActivo(); setMenuOpen(false); }}
            disabled={isToggling}
          >
            {isToggling ? "Cambiando..." : radicado.activo ? "Pausar monitoreo" : "Reactivar monitoreo"}
          </button>
          <button
            role="menuitem"
            onClick={() => { setMenuOpen(false); onDelete(); }}
            className={styles.menuDanger}
            disabled={isDeleting}
          >
            {isDeleting ? "Eliminando..." : "Eliminar"}
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
          {etiquetasNode}
        </div>
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
        {etiquetasNode}
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
