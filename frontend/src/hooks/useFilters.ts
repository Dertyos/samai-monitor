import { useState, useCallback, useMemo } from "react";
import type { RadicadoDTO } from "../lib/api";
import { getEspecialidad, getInstancia } from "../lib/radicadoHelpers";

const STORAGE_KEY = "radicadoFilters";

export interface FilterState {
  fuente: string[];        // ["samai", "rama_judicial", "siugj"]
  activo: string[];        // ["true", "false"]
  despacho: string[];      // multi-select
  ciudad: string[];        // multi-select
  especialidad: string[];  // multi-select
  instancia: string[];     // multi-select
  fechaDesde: string;      // ISO date
  fechaHasta: string;      // ISO date
}

const EMPTY_FILTERS: FilterState = {
  fuente: [],
  activo: [],
  despacho: [],
  ciudad: [],
  especialidad: [],
  instancia: [],
  fechaDesde: "",
  fechaHasta: "",
};

function loadFilters(): FilterState {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (raw) return { ...EMPTY_FILTERS, ...JSON.parse(raw) };
  } catch { /* ignore */ }
  return { ...EMPTY_FILTERS };
}

function saveFilters(filters: FilterState): void {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(filters));
}

/** Computes available options for each filter from the user's radicados. */
export function useFilterOptions(radicados: RadicadoDTO[]) {
  return useMemo(() => {
    const fuentes = new Set<string>();
    const activos = new Set<string>();
    const despachos = new Set<string>();
    const ciudades = new Set<string>();
    const especialidades = new Set<string>();
    const instancias = new Set<string>();

    for (const r of radicados) {
      if (r.fuente) fuentes.add(r.fuente);
      activos.add(String(r.activo));
      if (r.despacho) despachos.add(r.despacho);
      if (r.ciudad) ciudades.add(r.ciudad);
      // Especialidad e instancia se computan del radicado, no dependen de metadata del API
      especialidades.add(r.especialidad || getEspecialidad(r.radicado));
      instancias.add(r.instancia || getInstancia(r.radicado));
    }

    return {
      fuente: [...fuentes].sort(),
      activo: [...activos].sort(),
      despacho: [...despachos].sort(),
      ciudad: [...ciudades].sort(),
      especialidad: [...especialidades].sort(),
      instancia: [...instancias].sort(),
    };
  }, [radicados]);
}

export function useFilters() {
  const [filters, setFiltersRaw] = useState<FilterState>(loadFilters);

  const setFilters = useCallback((updater: FilterState | ((prev: FilterState) => FilterState)) => {
    setFiltersRaw((prev) => {
      const next = typeof updater === "function" ? updater(prev) : updater;
      saveFilters(next);
      return next;
    });
  }, []);

  const setFilter = useCallback(<K extends keyof FilterState>(key: K, value: FilterState[K]) => {
    setFilters((prev) => ({ ...prev, [key]: value }));
  }, [setFilters]);

  const toggleArrayFilter = useCallback((key: keyof FilterState, value: string) => {
    setFilters((prev) => {
      const arr = prev[key] as string[];
      const next = arr.includes(value) ? arr.filter((v) => v !== value) : [...arr, value];
      return { ...prev, [key]: next };
    });
  }, [setFilters]);

  const clearAll = useCallback(() => {
    setFilters({ ...EMPTY_FILTERS });
  }, [setFilters]);

  const activeCount = useMemo(() => {
    let count = 0;
    if (filters.fuente.length) count++;
    if (filters.activo.length) count++;
    if (filters.despacho.length) count++;
    if (filters.ciudad.length) count++;
    if (filters.especialidad.length) count++;
    if (filters.instancia.length) count++;
    if (filters.fechaDesde || filters.fechaHasta) count++;
    return count;
  }, [filters]);

  const hasFilters = activeCount > 0;

  /** Apply all active filters to a list of radicados. */
  const applyFilters = useCallback(
    (radicados: RadicadoDTO[]): RadicadoDTO[] => {
      return radicados.filter((r) => {
        if (filters.fuente.length && !filters.fuente.includes(r.fuente || "samai")) return false;
        if (filters.activo.length && !filters.activo.includes(String(r.activo))) return false;
        if (filters.despacho.length && !filters.despacho.includes(r.despacho || "")) return false;
        if (filters.ciudad.length && !filters.ciudad.includes(r.ciudad || "")) return false;
        if (filters.especialidad.length && !filters.especialidad.includes(r.especialidad || getEspecialidad(r.radicado))) return false;
        if (filters.instancia.length && !filters.instancia.includes(r.instancia || getInstancia(r.radicado))) return false;
        if (filters.fechaDesde) {
          const fecha = r.fechaUltimaActuacion || r.createdAt || "";
          if (fecha < filters.fechaDesde) return false;
        }
        if (filters.fechaHasta) {
          const fecha = r.fechaUltimaActuacion || r.createdAt || "";
          if (fecha > filters.fechaHasta) return false;
        }
        return true;
      });
    },
    [filters],
  );

  return {
    filters,
    setFilter,
    toggleArrayFilter,
    clearAll,
    activeCount,
    hasFilters,
    applyFilters,
  };
}
