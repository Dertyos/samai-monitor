import { useState, useEffect } from "react";
import { buscarProceso, buscarRamaJudicial, type RJProcesoDTO } from "../lib/api";
import styles from "./AddRadicadoModal.module.css";

interface Props {
  onAdd: (radicado: string, alias: string, fuente: string, idProceso?: number) => void;
  onClose: () => void;
  error: string | null;
  loading: boolean;
}

interface SamaiSearchResult {
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
 * Soporta dos fuentes:
 * - SAMAI: búsqueda por nombre/número parcial (jurisdicción contencioso-administrativa)
 * - Rama Judicial: búsqueda CPNU por número de radicado (civil, penal, familia, tutelas, etc.)
 */
export default function AddRadicadoModal({ onAdd, onClose, error, loading }: Props) {
  const [fuente, setFuente] = useState<"samai" | "rama_judicial">("samai");

  // Shared
  const [radicado, setRadicado] = useState("");
  const [alias, setAlias] = useState("");

  // SAMAI search
  const [searchQuery, setSearchQuery] = useState("");
  const [samaiResults, setSamaiResults] = useState<SamaiSearchResult[]>([]);

  // Rama Judicial search + selected process
  const [rjResults, setRjResults] = useState<RJProcesoDTO[]>([]);
  const [selectedRj, setSelectedRj] = useState<RJProcesoDTO | null>(null);

  const [searching, setSearching] = useState(false);
  const [searchError, setSearchError] = useState<string | null>(null);
  const [hasSearched, setHasSearched] = useState(false);

  useEffect(() => {
    const handle = (e: KeyboardEvent) => {
      if (e.key === "Escape" && !loading) onClose();
    };
    document.addEventListener("keydown", handle);
    return () => document.removeEventListener("keydown", handle);
  }, [onClose, loading]);

  // Reset search state when switching fuente
  useEffect(() => {
    setSearchQuery("");
    setSamaiResults([]);
    setRjResults([]);
    setSelectedRj(null);
    setHasSearched(false);
    setSearchError(null);
    setRadicado("");
  }, [fuente]);

  const digits = radicado.replace(/\D/g, "");
  const isValid = digits.length === 23;

  // For Rama Judicial: also need a selected process
  const canSubmit = isValid && (fuente === "samai" || selectedRj !== null);

  const handleSearch = async () => {
    if (!searchQuery.trim()) return;
    setSearching(true);
    setSearchError(null);
    setHasSearched(true);
    setSamaiResults([]);
    setRjResults([]);
    try {
      if (fuente === "samai") {
        const results = await buscarProceso(searchQuery.trim()) as SamaiSearchResult[];
        setSamaiResults(results);
      } else {
        const results = await buscarRamaJudicial(searchQuery.trim());
        setRjResults(results);
        // Auto-fill radicado from first result
        if (results.length > 0) {
          setRadicado(formatRadicadoInput(results[0].llaveProceso));
        }
        // Auto-select if only one result or all from same radicado (SIUGJ)
        if (results.length === 1) {
          setSelectedRj(results[0]);
        }
      }
    } catch (err) {
      setSearchError(err instanceof Error ? err.message : "Error en busqueda");
    } finally {
      setSearching(false);
    }
  };

  const handleSelectSamai = (result: SamaiSearchResult) => {
    setRadicado(formatRadicadoInput(result.llaveProceso));
    setSamaiResults([]);
    setSearchQuery("");
    setHasSearched(false);
  };

  const handleSelectRj = (result: RJProcesoDTO) => {
    setSelectedRj(result);
    setRadicado(formatRadicadoInput(result.llaveProceso));
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (fuente === "rama_judicial" && selectedRj) {
      if (selectedRj.sistema === "siugj") {
        // SIUGJ: no idProceso — the radicado itself is the identifier
        onAdd(digits, alias.trim(), "siugj");
      } else {
        // CPNU: pass idProceso for fast future lookups
        onAdd(digits, alias.trim(), "rama_judicial", selectedRj.idProceso ?? undefined);
      }
    } else {
      onAdd(digits, alias.trim(), "samai");
    }
  };

  // Track where mousedown started so text-selection drags don't close the modal
  const mouseDownOnOverlay = { current: false };

  return (
    <div
      className="modal-overlay"
      onMouseDown={(e) => { mouseDownOnOverlay.current = e.target === e.currentTarget; }}
      onMouseUp={(e) => { if (mouseDownOnOverlay.current && e.target === e.currentTarget && !loading) onClose(); }}
      onClick={(e) => e.stopPropagation()}
    >
      <div className="modal" onMouseDown={(e) => e.stopPropagation()}>
        <h3>Agregar Radicado</h3>

        {/* Source selector */}
        <div className={styles.sourceTabs}>
          <button
            type="button"
            className={fuente === "samai" ? styles.sourceTabActive : styles.sourceTab}
            onClick={() => setFuente("samai")}
          >
            SAMAI
          </button>
          <button
            type="button"
            className={fuente === "rama_judicial" ? styles.sourceTabActive : styles.sourceTab}
            onClick={() => setFuente("rama_judicial")}
          >
            Rama Judicial
          </button>
        </div>

        {/* Search section */}
        <div className={styles.searchSection}>
          <label>
            {fuente === "samai" ? "Buscar en SAMAI (opcional)" : "Buscar por radicado en CPNU"}
            <div style={{ display: "flex", gap: "0.5rem" }}>
              <input
                type="text"
                placeholder={fuente === "samai" ? "Numero de proceso..." : "73001-23-33-000-2019-00343-00"}
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

          {/* SAMAI results */}
          {samaiResults.length > 0 && (
            <div className={styles.searchResults}>
              {samaiResults.map((r, i) => (
                <div
                  key={`${r.llaveProceso}-${i}`}
                  className={styles.searchItem}
                  onClick={() => handleSelectSamai(r)}
                >
                  <span className={styles.searchItemRadicado}>{r.llaveProceso}</span>
                  {r.despacho && (
                    <span className={styles.searchItemDespacho}>{r.despacho}</span>
                  )}
                </div>
              ))}
            </div>
          )}

          {/* Rama Judicial results (CPNU + SIUGJ fallback) */}
          {rjResults.length > 0 && (
            <div className={styles.searchResults}>
              <p className={styles.rjHint}>Selecciona el despacho correcto:</p>
              {rjResults.map((r, i) => (
                <div
                  key={`${r.llaveProceso}-${i}`}
                  className={`${styles.searchItem} ${selectedRj?.llaveProceso === r.llaveProceso ? styles.searchItemSelected : ""}`}
                  onClick={() => handleSelectRj(r)}
                >
                  <span className={styles.searchItemRadicado}>
                    {r.despacho}
                    <span className={r.sistema === "siugj" ? styles.badgeSiugj : styles.badgeCpnu}>
                      {r.sistema === "siugj" ? "vía SIUGJ" : "vía CPNU"}
                    </span>
                  </span>
                  {r.sujetosProcesales && (
                    <span className={styles.searchItemDespacho}>{r.sujetosProcesales}</span>
                  )}
                  {r.fechaUltimaActuacion && (
                    <span className={styles.searchItemMeta}>
                      Ultima actuacion: {r.fechaUltimaActuacion.slice(0, 10)}
                    </span>
                  )}
                </div>
              ))}
            </div>
          )}

          {hasSearched && samaiResults.length === 0 && rjResults.length === 0 && !searching && !searchError && (
            <p className={styles.noResults}>Sin resultados</p>
          )}
        </div>

        {fuente === "samai" && (
          <p className={styles.divider}>o ingresa el numero directamente</p>
        )}

        <form onSubmit={handleSubmit}>
          {fuente === "samai" && (
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
                <span className="input-hint">{digits.length}/23 digitos</span>
              )}
            </label>
          )}
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
            <button type="submit" className="primary" disabled={loading || !canSubmit}>
              {loading ? "Agregando..." : "Agregar"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
