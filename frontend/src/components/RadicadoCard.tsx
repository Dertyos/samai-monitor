import type { RadicadoDTO } from "../lib/api";

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
    <div className={`radicado-card ${isSelected ? "selected" : ""}`}>
      <div className="card-header" onClick={onSelect}>
        <span className="radicado-fmt">{radicado.radicadoFormato}</span>
        {radicado.alias && <span className="alias">{radicado.alias}</span>}
      </div>
      <div className="card-body">
        <span className="meta">
          Última actuación: #{radicado.ultimoOrden}
        </span>
        <span className={`status ${radicado.activo ? "active" : "inactive"}`}>
          {radicado.activo ? "Activo" : "Inactivo"}
        </span>
      </div>
      <div className="card-actions">
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
