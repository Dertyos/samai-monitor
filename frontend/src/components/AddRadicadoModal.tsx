import { useState } from "react";
import { buscarProceso } from "../lib/api";
import styles from "./AddRadicadoModal.module.css";

interface Props {
  onAdd: (radicado: string, alias: string) => void;
  onClose: () => void;
  error: string | null;
  loading: boolean;
}

interface SearchResult {
  llaveProceso: string;
  despacho: string;
}

/** Auto-format radicado input: strips non-digits and inserts dashes. */
function formatRadicadoInput(value: string): string {
  const digits = value.replace(/\D/g, "").slice(0, 23);
  const parts = [
    digits.slice(0, 5),
    digits.slice(5, 7),
    digits.slice(7, 9),
    digits.slice(9, 12),
    digits.slice(12, 16),
    digits.slice(16, 21),
    digits.slice(21, 23),
  ];
  return parts.filter(Boolean).join("-");
}

/**
 * AddRadicadoModal — modal para agregar un radicado a monitorear.
 *
 * Dos formas de ingresar el radicado:
 * 1. Buscar en SAMAI por numero parcial y seleccionar de resultados
 * 2. Escribir el numero completo (23 digitos) directamente
 *
 * Reutilizable: recibe callbacks onAdd y onClose.
 */
export default function AddRadicadoModal({ onAdd, onClose, error, loading }: Props) {
  const [radicado, setRadicado] = useState("");
  const [alias, setAlias] = useState("");
  const [searchQuery, setSearchQuery] = useState("");
  const [searchResults, setSearchResults] = useState<SearchResult[]>([]);
  const [searching, setSearching] = useState(false);
  const [searchError, setSearchError] = useState<string | null>(null);
  const [hasSearched, setHasSearched] = useState(false);

  const digits = radicado.replace(/\D/g, "");
  const isValid = digits.length === 23;

  const handleSearch = async () => {
    if (!searchQuery.trim()) return;
    setSearching(true);
    setSearchError(null);
    setHasSearched(true);
    try {
      const results = await buscarProceso(searchQuery.trim()) as SearchResult[];
      setSearchResults(results);
    } catch (err) {
      setSearchError(err instanceof Error ? err.message : "Error en busqueda");
    } finally {
      setSearching(false);
    }
  };

  const handleSelectResult = (result: SearchResult) => {
    setRadicado(formatRadicadoInput(result.llaveProceso));
    setSearchResults([]);
    setSearchQuery("");
    setHasSearched(false);
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onAdd(digits, alias.trim());
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal" onClick={(e) => e.stopPropagation()}>
        <h3>Agregar Radicado</h3>

        {/* Seccion de busqueda */}
        <div className={styles.searchSection}>
          <label>
            Buscar en SAMAI (opcional)
            <div style={{ display: "flex", gap: "0.5rem" }}>
              <input
                type="text"
                placeholder="Numero de proceso..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                onKeyDown={(e) => { if (e.key === "Enter") { e.preventDefault(); handleSearch(); }}}
              />
              <button
                type="button"
                className={`primary ${styles.searchBtn}`}
                onClick={handleSearch}
                disabled={searching || !searchQuery.trim()}
              >
                {searching ? "..." : "Buscar"}
              </button>
            </div>
          </label>

          {searchError && <div className="error">{searchError}</div>}

          {searchResults.length > 0 && (
            <div className={styles.searchResults}>
              {searchResults.map((r, i) => (
                <div
                  key={`${r.llaveProceso}-${i}`}
                  className={styles.searchItem}
                  onClick={() => handleSelectResult(r)}
                >
                  <span className={styles.searchItemRadicado}>{r.llaveProceso}</span>
                  {r.despacho && (
                    <span className={styles.searchItemDespacho}>{r.despacho}</span>
                  )}
                </div>
              ))}
            </div>
          )}

          {hasSearched && searchResults.length === 0 && !searching && !searchError && (
            <p className={styles.noResults}>Sin resultados</p>
          )}
        </div>

        <p className={styles.divider}>o ingresa el numero directamente</p>

        <form onSubmit={handleSubmit}>
          <label>
            Numero de radicado
            <input
              type="text"
              placeholder="73001-23-33-000-2019-00343-00"
              value={radicado}
              onChange={(e) => setRadicado(formatRadicadoInput(e.target.value))}
              required
              className={radicado && !isValid ? "input-warning" : ""}
            />
            {radicado && !isValid && (
              <span className="input-hint">
                {digits.length}/23 digitos
              </span>
            )}
          </label>
          <label>
            Alias (opcional)
            <input
              type="text"
              placeholder="Caso Aviles"
              value={alias}
              onChange={(e) => setAlias(e.target.value)}
            />
          </label>
          {error && <div className="error">{error}</div>}
          <div className="modal-actions">
            <button type="button" onClick={onClose} className="btn-secondary">
              Cancelar
            </button>
            <button type="submit" className="primary" disabled={loading || !isValid}>
              {loading ? "Agregando..." : "Agregar"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
