import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  getRadicados,
  addRadicado,
  deleteRadicado,
  getAlertas,
  type RadicadoDTO,
} from "../lib/api";
import AddRadicadoModal from "../components/AddRadicadoModal";
import RadicadoCard from "../components/RadicadoCard";
import AlertasList from "../components/AlertasList";
import { useTheme } from "../hooks/useTheme";

interface Props {
  email: string | null;
  onSignOut: () => void;
  onViewHistorial: (radicado: RadicadoDTO) => void;
}

export default function Dashboard({ email, onSignOut, onViewHistorial }: Props) {
  const [showAddModal, setShowAddModal] = useState(false);
  const queryClient = useQueryClient();
  const { theme, toggle: toggleTheme } = useTheme();

  const radicadosQuery = useQuery({
    queryKey: ["radicados"],
    queryFn: getRadicados,
  });

  const alertasQuery = useQuery({
    queryKey: ["alertas"],
    queryFn: getAlertas,
  });

  const addMutation = useMutation({
    mutationFn: ({ radicado, alias }: { radicado: string; alias: string }) =>
      addRadicado(radicado, alias),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["radicados"] });
      setShowAddModal(false);
    },
  });

  const deleteMutation = useMutation({
    mutationFn: deleteRadicado,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["radicados"] });
    },
  });

  return (
    <div className="dashboard">
      <header>
        <div className="header-left">
          <h1>SAMAI Monitor</h1>
        </div>
        <div className="header-right">
          <span className="email">{email}</span>
          <button onClick={toggleTheme} className="theme-toggle" title="Cambiar tema">
            {theme === "light" ? "\u{1F319}" : "\u{2600}\u{FE0F}"}
          </button>
          <button onClick={onSignOut} className="btn-secondary">
            Cerrar sesión
          </button>
        </div>
      </header>

      <main>
        <section className="section">
          <div className="section-header">
            <h2>Mis Radicados</h2>
            <button onClick={() => setShowAddModal(true)} className="primary">
              + Agregar
            </button>
          </div>

          {radicadosQuery.isLoading && (
            <div className="loading-container">
              <div className="spinner" />
              <p>Cargando radicados...</p>
            </div>
          )}
          {radicadosQuery.error && (
            <p className="error">
              Error: {radicadosQuery.error instanceof Error ? radicadosQuery.error.message : "Error"}
            </p>
          )}

          <div className="radicados-grid">
            {radicadosQuery.data?.map((r: RadicadoDTO) => (
              <RadicadoCard
                key={r.radicado}
                radicado={r}
                isSelected={false}
                onSelect={() => onViewHistorial(r)}
                onDelete={() => {
                  if (confirm(`¿Dejar de monitorear ${r.radicadoFormato}?`)) {
                    deleteMutation.mutate(r.radicado);
                  }
                }}
                isDeleting={
                  deleteMutation.isPending &&
                  deleteMutation.variables === r.radicado
                }
              />
            ))}
            {radicadosQuery.data?.length === 0 && (
              <div className="empty-state">
                <p className="empty-state-icon">&#x1F4CB;</p>
                <p className="empty-state-text">No tienes radicados monitoreados</p>
                <p className="empty-state-hint">Agrega uno con el botón "+ Agregar" para empezar</p>
              </div>
            )}
          </div>
        </section>

        <section className="section">
          <h2>Alertas Recientes</h2>
          {alertasQuery.isLoading && (
            <div className="loading-container">
              <div className="spinner" />
              <p>Cargando alertas...</p>
            </div>
          )}
          {alertasQuery.data && <AlertasList alertas={alertasQuery.data} />}
          {alertasQuery.data?.length === 0 && (
            <div className="empty-state">
              <p className="empty-state-icon">&#x1F514;</p>
              <p className="empty-state-text">Sin alertas recientes</p>
              <p className="empty-state-hint">Las alertas aparecen cuando el monitor detecta nuevas actuaciones</p>
            </div>
          )}
        </section>
      </main>

      {showAddModal && (
        <AddRadicadoModal
          onAdd={(radicado, alias) => addMutation.mutate({ radicado, alias })}
          onClose={() => setShowAddModal(false)}
          error={
            addMutation.error instanceof Error
              ? addMutation.error.message
              : null
          }
          loading={addMutation.isPending}
        />
      )}
    </div>
  );
}
