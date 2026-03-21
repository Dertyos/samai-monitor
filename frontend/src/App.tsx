import { useState } from "react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useAuth } from "./hooks/useAuth";
import Login from "./pages/Login";
import Dashboard from "./pages/Dashboard";
import DetalleRadicado from "./pages/DetalleRadicado";
import type { RadicadoDTO } from "./lib/api";
import "./App.css";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: { staleTime: 30_000, retry: 1 },
  },
});

function AppContent() {
  const auth = useAuth();
  const [viewingDetalle, setViewingDetalle] = useState<RadicadoDTO | null>(
    null
  );

  if (auth.isLoading) {
    return (
      <div className="loading-screen">
        <h1>SAMAI Monitor</h1>
        <div className="spinner" />
        <p>Cargando...</p>
      </div>
    );
  }

  if (!auth.isAuthenticated) {
    return (
      <Login
        onSignIn={auth.signIn}
        onSignUp={auth.signUp}
        onConfirm={auth.confirmSignUp}
        error={auth.error}
      />
    );
  }

  if (viewingDetalle) {
    return (
      <DetalleRadicado
        radicado={viewingDetalle.radicado}
        radicadoFormato={viewingDetalle.radicadoFormato}
        alias={viewingDetalle.alias}
        onBack={() => setViewingDetalle(null)}
      />
    );
  }

  return (
    <Dashboard
      email={auth.email}
      onSignOut={auth.signOut}
      onViewHistorial={setViewingDetalle}
    />
  );
}

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <AppContent />
    </QueryClientProvider>
  );
}
