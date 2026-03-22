import { Component } from "react";
import type { ReactNode, ErrorInfo } from "react";

interface Props {
  children: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

/**
 * ErrorBoundary — atrapa errores de renderizado en React.
 *
 * Muestra un fallback amigable en vez de pantalla blanca.
 * Solo atrapa errores en render/lifecycle, no en event handlers.
 */
export default class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, info: ErrorInfo): void {
    console.error("ErrorBoundary caught:", error, info.componentStack);
  }

  render(): ReactNode {
    if (this.state.hasError) {
      return (
        <div style={{
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
          minHeight: "100vh",
          padding: "2rem",
          textAlign: "center",
          fontFamily: "system-ui, sans-serif",
        }}>
          <h1 style={{ fontSize: "1.5rem", marginBottom: "0.5rem" }}>
            Algo salio mal
          </h1>
          <p style={{ color: "#666", marginBottom: "1rem", maxWidth: "400px" }}>
            Ocurrio un error inesperado. Intenta recargar la pagina.
          </p>
          {this.state.error && (
            <pre style={{
              background: "#f5f5f5",
              padding: "0.75rem",
              borderRadius: "6px",
              fontSize: "0.75rem",
              maxWidth: "500px",
              overflow: "auto",
              marginBottom: "1rem",
              color: "#c00",
            }}>
              {this.state.error.message}
            </pre>
          )}
          <button
            onClick={() => window.location.reload()}
            style={{
              padding: "0.5rem 1.5rem",
              background: "#2563eb",
              color: "white",
              border: "none",
              borderRadius: "6px",
              cursor: "pointer",
              fontSize: "0.9rem",
            }}
          >
            Recargar pagina
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}
