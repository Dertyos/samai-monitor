import { createContext, useContext, useState, useCallback } from "react";
import styles from "../components/Toast.module.css";

/**
 * Toast system — notificaciones flotantes reutilizables.
 *
 * Uso:
 *   1. Envolver la app con <ToastProvider>
 *   2. En cualquier componente: const toast = useToast()
 *   3. toast.success("Radicado agregado")
 *      toast.error("Error al eliminar")
 *      toast.info("Codigo enviado al correo")
 *
 * Configuracion:
 *   - duration: ms antes de auto-dismiss (default 4000)
 *   - Los toasts se apilan arriba-derecha
 *   - Se pueden cerrar manualmente con X
 */

type ToastType = "success" | "error" | "info";

interface Toast {
  id: number;
  message: string;
  type: ToastType;
  exiting: boolean;
}

interface ToastContextValue {
  success: (message: string) => void;
  error: (message: string) => void;
  info: (message: string) => void;
}

const ToastContext = createContext<ToastContextValue | null>(null);

let nextId = 0;
const DURATION = 4000;
const EXIT_DURATION = 150;

export function ToastProvider({ children }: { children: React.ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([]);

  const removeToast = useCallback((id: number) => {
    // Trigger exit animation
    setToasts((prev) => prev.map((t) => (t.id === id ? { ...t, exiting: true } : t)));
    // Remove after animation
    setTimeout(() => {
      setToasts((prev) => prev.filter((t) => t.id !== id));
    }, EXIT_DURATION);
  }, []);

  const addToast = useCallback(
    (message: string, type: ToastType) => {
      const id = nextId++;
      setToasts((prev) => [...prev, { id, message, type, exiting: false }]);
      setTimeout(() => removeToast(id), DURATION);
    },
    [removeToast],
  );

  const value: ToastContextValue = {
    success: useCallback((msg: string) => addToast(msg, "success"), [addToast]),
    error: useCallback((msg: string) => addToast(msg, "error"), [addToast]),
    info: useCallback((msg: string) => addToast(msg, "info"), [addToast]),
  };

  return (
    <ToastContext.Provider value={value}>
      {children}
      {toasts.length > 0 && (
        <div className={styles.container}>
          {toasts.map((t) => (
            <div
              key={t.id}
              className={`${styles.toast} ${styles[t.type]} ${t.exiting ? styles.exiting : ""}`}
            >
              <span>{t.message}</span>
              <button className={styles.dismiss} onClick={() => removeToast(t.id)}>
                &times;
              </button>
            </div>
          ))}
        </div>
      )}
    </ToastContext.Provider>
  );
}

export function useToast(): ToastContextValue {
  const ctx = useContext(ToastContext);
  if (!ctx) {
    throw new Error("useToast must be used within a ToastProvider");
  }
  return ctx;
}
