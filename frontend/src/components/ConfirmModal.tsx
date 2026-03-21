import styles from "./ConfirmModal.module.css";

/**
 * ConfirmModal — dialogo de confirmacion reutilizable.
 *
 * Reemplaza window.confirm() con un modal que respeta el tema.
 * Usa los estilos globales de modal.css (overlay, modal, modal-actions).
 *
 * Props:
 * - title: titulo del dialogo
 * - message: descripcion/advertencia
 * - confirmLabel: texto del boton de confirmacion (default "Confirmar")
 * - cancelLabel: texto del boton de cancelar (default "Cancelar")
 * - variant: "danger" | "default" (cambia el color del boton)
 * - onConfirm: callback al confirmar
 * - onCancel: callback al cancelar
 * - loading: deshabilita botones mientras se procesa
 */
interface Props {
  title: string;
  message: string;
  confirmLabel?: string;
  cancelLabel?: string;
  variant?: "danger" | "default";
  onConfirm: () => void;
  onCancel: () => void;
  loading?: boolean;
}

export default function ConfirmModal({
  title,
  message,
  confirmLabel = "Confirmar",
  cancelLabel = "Cancelar",
  variant = "default",
  onConfirm,
  onCancel,
  loading = false,
}: Props) {
  return (
    <div className="modal-overlay" onClick={onCancel}>
      <div
        className={`modal ${variant === "danger" ? styles.danger : ""}`}
        onClick={(e) => e.stopPropagation()}
      >
        <h3 className={styles.title}>{title}</h3>
        <p className={styles.message}>{message}</p>
        <div className="modal-actions">
          <button onClick={onCancel} className="btn-secondary" disabled={loading}>
            {cancelLabel}
          </button>
          <button
            onClick={onConfirm}
            className={variant === "danger" ? "btn-danger" : "primary"}
            disabled={loading}
          >
            {loading ? "..." : confirmLabel}
          </button>
        </div>
      </div>
    </div>
  );
}
