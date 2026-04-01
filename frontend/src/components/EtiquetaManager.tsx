import { useState, useEffect } from "react";
import type { EtiquetaDTO } from "../lib/api";
import styles from "./EtiquetaManager.module.css";

interface Props {
  etiquetas: EtiquetaDTO[];
  onClose: () => void;
  onCreate: (nombre: string, color: string) => void;
  onUpdate: (etiquetaId: string, nombre: string, color: string) => void;
  onDelete: (etiquetaId: string) => void;
  isCreating: boolean;
  isUpdating: boolean;
  isDeleting: boolean;
}

const DEFAULT_COLORS = [
  "#dc3545", "#f59e0b", "#10b981", "#1a73e8",
  "#8b5cf6", "#ec4899", "#6b7280", "#059669",
];

export default function EtiquetaManager({
  etiquetas,
  onClose,
  onCreate,
  onUpdate,
  onDelete,
  isCreating,
  isUpdating,
  isDeleting,
}: Props) {
  const [nombre, setNombre] = useState("");
  const [color, setColor] = useState(DEFAULT_COLORS[0]);
  const [editId, setEditId] = useState<string | null>(null);
  const [editNombre, setEditNombre] = useState("");
  const [editColor, setEditColor] = useState("");

  useEffect(() => {
    const handle = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    document.addEventListener("keydown", handle);
    return () => document.removeEventListener("keydown", handle);
  }, [onClose]);

  const handleCreate = () => {
    if (!nombre.trim()) return;
    onCreate(nombre.trim(), color);
    setNombre("");
    setColor(DEFAULT_COLORS[Math.floor(Math.random() * DEFAULT_COLORS.length)]);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter") handleCreate();
  };

  const startEdit = (etq: EtiquetaDTO) => {
    setEditId(etq.etiquetaId);
    setEditNombre(etq.nombre);
    setEditColor(etq.color);
  };

  const handleUpdate = () => {
    if (!editId || !editNombre.trim()) return;
    onUpdate(editId, editNombre.trim(), editColor);
    setEditId(null);
  };

  const handleEditKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter") handleUpdate();
    if (e.key === "Escape") setEditId(null);
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal" onClick={(e) => e.stopPropagation()} style={{ maxWidth: 480 }}>
        <div className={styles.headerRow}>
          <h3>Mis Etiquetas</h3>
          <button onClick={onClose} className="btn-secondary" style={{ padding: "0.25rem 0.5rem" }}>
            Cerrar
          </button>
        </div>

        {etiquetas.length === 0 ? (
          <p className={styles.emptyText}>
            No tienes etiquetas. Crea una para organizar tus casos.
          </p>
        ) : (
          <div className={styles.list}>
            {etiquetas.map((etq) =>
              editId === etq.etiquetaId ? (
                <div key={etq.etiquetaId} className={styles.item}>
                  <input
                    type="color"
                    value={editColor}
                    onChange={(e) => setEditColor(e.target.value)}
                    className={styles.colorInput}
                  />
                  <input
                    type="text"
                    value={editNombre}
                    onChange={(e) => setEditNombre(e.target.value)}
                    onKeyDown={handleEditKeyDown}
                    autoFocus
                    className="input"
                    style={{ flex: 1 }}
                  />
                  <div className={styles.itemActions}>
                    <button
                      onClick={handleUpdate}
                      className={styles.iconBtn}
                      disabled={isUpdating}
                      title="Guardar"
                    >
                      {isUpdating ? "..." : "OK"}
                    </button>
                    <button
                      onClick={() => setEditId(null)}
                      className={styles.iconBtn}
                      title="Cancelar"
                    >
                      X
                    </button>
                  </div>
                </div>
              ) : (
                <div key={etq.etiquetaId} className={styles.item}>
                  <span
                    className={styles.colorDot}
                    style={{ backgroundColor: etq.color }}
                  />
                  <span className={styles.itemName}>{etq.nombre}</span>
                  <div className={styles.itemActions}>
                    <button
                      onClick={() => startEdit(etq)}
                      className={styles.iconBtn}
                      title="Editar"
                    >
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M11 4H4a2 2 0 00-2 2v14a2 2 0 002 2h14a2 2 0 002-2v-7"/><path d="M18.5 2.5a2.12 2.12 0 013 3L12 15l-4 1 1-4 9.5-9.5z"/></svg>
                    </button>
                    <button
                      onClick={() => onDelete(etq.etiquetaId)}
                      className={`${styles.iconBtn} ${styles.iconBtnDanger}`}
                      disabled={isDeleting}
                      title="Eliminar"
                    >
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 01-2 2H7a2 2 0 01-2-2V6m3 0V4a2 2 0 012-2h4a2 2 0 012 2v2"/></svg>
                    </button>
                  </div>
                </div>
              )
            )}
          </div>
        )}

        <div className={styles.form}>
          <div className={styles.formRow}>
            <input
              type="color"
              value={color}
              onChange={(e) => setColor(e.target.value)}
              className={styles.colorInput}
              title="Color de la etiqueta"
            />
            <input
              type="text"
              value={nombre}
              onChange={(e) => setNombre(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Nueva etiqueta..."
              className="input"
              maxLength={30}
            />
            <button
              onClick={handleCreate}
              className="primary"
              disabled={isCreating || !nombre.trim()}
            >
              {isCreating ? "..." : "+ Crear"}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
