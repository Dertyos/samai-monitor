import { useState, useRef, useEffect, useMemo } from "react";
import type { FilterState } from "../hooks/useFilters";
import styles from "./FilterBar.module.css";

interface FilterBarProps {
  filters: FilterState;
  options: {
    fuente: string[];
    activo: string[];
    despacho: string[];
    ciudad: string[];
    especialidad: string[];
    instancia: string[];
  };
  activeCount: number;
  onToggle: (key: keyof FilterState, value: string) => void;
  onSetFilter: <K extends keyof FilterState>(key: K, value: FilterState[K]) => void;
  onClearAll: () => void;
}

const FUENTE_LABELS: Record<string, string> = {
  samai: "SAMAI",
  rama_judicial: "Rama J.",
  siugj: "SIUGJ",
};

const ACTIVO_LABELS: Record<string, string> = {
  true: "Activo",
  false: "Pausado",
};

type FilterCategory = "fuente" | "activo" | "despacho" | "ciudad" | "especialidad" | "instancia" | "fecha";

const CATEGORY_LABELS: Record<FilterCategory, string> = {
  fuente: "Fuente",
  activo: "Estado",
  despacho: "Despacho",
  ciudad: "Ciudad",
  especialidad: "Especialidad",
  instancia: "Instancia",
  fecha: "Fecha",
};

export default function FilterBar({
  filters,
  options,
  activeCount,
  onToggle,
  onSetFilter,
  onClearAll,
}: FilterBarProps) {
  const [openCategory, setOpenCategory] = useState<FilterCategory | null>(null);
  const [popoverSearch, setPopoverSearch] = useState("");
  const popoverRef = useRef<HTMLDivElement>(null);
  const buttonRef = useRef<HTMLButtonElement>(null);

  // Close popover on click outside
  useEffect(() => {
    if (!openCategory) return;
    const handleClick = (e: MouseEvent) => {
      if (
        popoverRef.current && !popoverRef.current.contains(e.target as Node) &&
        buttonRef.current && !buttonRef.current.contains(e.target as Node)
      ) {
        setOpenCategory(null);
        setPopoverSearch("");
      }
    };
    document.addEventListener("mousedown", handleClick);
    return () => document.removeEventListener("mousedown", handleClick);
  }, [openCategory]);

  // Available categories: hide those with <= 1 option
  const availableCategories = useMemo(() => {
    const cats: FilterCategory[] = [];
    if (options.fuente.length > 1) cats.push("fuente");
    if (options.activo.length > 1) cats.push("activo");
    if (options.despacho.length > 1) cats.push("despacho");
    if (options.ciudad.length > 1) cats.push("ciudad");
    if (options.especialidad.length > 1) cats.push("especialidad");
    if (options.instancia.length > 1) cats.push("instancia");
    cats.push("fecha"); // always available
    return cats;
  }, [options]);

  // Build active chip descriptors
  const chips: { key: FilterCategory; label: string; value: string }[] = [];
  for (const v of filters.fuente) {
    chips.push({ key: "fuente", label: "Fuente", value: FUENTE_LABELS[v] || v });
  }
  for (const v of filters.activo) {
    chips.push({ key: "activo", label: "Estado", value: ACTIVO_LABELS[v] || v });
  }
  for (const v of filters.despacho) {
    chips.push({ key: "despacho", label: "Despacho", value: v.length > 30 ? v.slice(0, 30) + "..." : v });
  }
  for (const v of filters.ciudad) {
    chips.push({ key: "ciudad", label: "Ciudad", value: v });
  }
  for (const v of filters.especialidad) {
    chips.push({ key: "especialidad", label: "Especialidad", value: v });
  }
  for (const v of filters.instancia) {
    chips.push({ key: "instancia", label: "Instancia", value: v });
  }
  if (filters.fechaDesde || filters.fechaHasta) {
    const parts = [];
    if (filters.fechaDesde) parts.push(`desde ${filters.fechaDesde}`);
    if (filters.fechaHasta) parts.push(`hasta ${filters.fechaHasta}`);
    chips.push({ key: "fecha", label: "Fecha", value: parts.join(" ") });
  }

  const handleRemoveChip = (chip: { key: FilterCategory; value: string }) => {
    if (chip.key === "fecha") {
      onSetFilter("fechaDesde", "");
      onSetFilter("fechaHasta", "");
    } else if (chip.key === "fuente") {
      const original = Object.entries(FUENTE_LABELS).find(([, l]) => l === chip.value)?.[0] || chip.value;
      onToggle("fuente", original);
    } else if (chip.key === "activo") {
      const original = Object.entries(ACTIVO_LABELS).find(([, l]) => l === chip.value)?.[0] || chip.value;
      onToggle("activo", original);
    } else {
      // For despacho/ciudad/especialidad the value might be truncated
      const fullVal = (filters[chip.key] as string[]).find((v) =>
        chip.value.endsWith("...") ? v.startsWith(chip.value.slice(0, -3)) : v === chip.value,
      );
      if (fullVal) onToggle(chip.key, fullVal);
    }
  };

  const toggleCategory = (cat: FilterCategory) => {
    setOpenCategory((prev) => (prev === cat ? null : cat));
    setPopoverSearch("");
  };

  const renderPopoverContent = () => {
    if (!openCategory) return null;

    if (openCategory === "fecha") {
      return (
        <div className={styles.popoverContent}>
          <label className={styles.dateLabel}>
            Desde
            <input
              type="date"
              className={styles.dateInput}
              value={filters.fechaDesde}
              onChange={(e) => onSetFilter("fechaDesde", e.target.value)}
            />
          </label>
          <label className={styles.dateLabel}>
            Hasta
            <input
              type="date"
              className={styles.dateInput}
              value={filters.fechaHasta}
              onChange={(e) => onSetFilter("fechaHasta", e.target.value)}
            />
          </label>
          <div className={styles.datePresets}>
            <button
              type="button"
              className={styles.presetBtn}
              onClick={() => {
                const d = new Date();
                d.setDate(d.getDate() - 7);
                onSetFilter("fechaDesde", d.toISOString().slice(0, 10));
                onSetFilter("fechaHasta", "");
              }}
            >
              Ultima semana
            </button>
            <button
              type="button"
              className={styles.presetBtn}
              onClick={() => {
                const d = new Date();
                d.setMonth(d.getMonth() - 1);
                onSetFilter("fechaDesde", d.toISOString().slice(0, 10));
                onSetFilter("fechaHasta", "");
              }}
            >
              Ultimo mes
            </button>
            <button
              type="button"
              className={styles.presetBtn}
              onClick={() => {
                const d = new Date();
                d.setFullYear(d.getFullYear() - 1);
                onSetFilter("fechaDesde", d.toISOString().slice(0, 10));
                onSetFilter("fechaHasta", "");
              }}
            >
              Ultimo año
            </button>
          </div>
        </div>
      );
    }

    // Array-based filters
    const key = openCategory as "fuente" | "activo" | "despacho" | "ciudad" | "especialidad";
    const allOptions = options[key] || [];
    const selected = filters[key] as string[];
    const labels = key === "fuente" ? FUENTE_LABELS : key === "activo" ? ACTIVO_LABELS : null;

    const needsSearch = allOptions.length > 5;
    const filtered = popoverSearch
      ? allOptions.filter((o) => {
          const display = labels ? labels[o] || o : o;
          return display.toLowerCase().includes(popoverSearch.toLowerCase());
        })
      : allOptions;

    return (
      <div className={styles.popoverContent}>
        {needsSearch && (
          <input
            type="text"
            className={styles.popoverSearch}
            placeholder="Buscar..."
            value={popoverSearch}
            onChange={(e) => setPopoverSearch(e.target.value)}
            autoFocus
          />
        )}
        <div className={styles.optionsList}>
          {filtered.map((opt) => {
            const isSelected = selected.includes(opt);
            const display = labels ? labels[opt] || opt : opt;
            return (
              <button
                key={opt}
                type="button"
                className={`${styles.optionItem} ${isSelected ? styles.optionSelected : ""}`}
                onClick={() => onToggle(key, opt)}
              >
                <span className={styles.optionCheck}>{isSelected ? "\u2713" : ""}</span>
                <span className={styles.optionLabel}>{display}</span>
              </button>
            );
          })}
          {filtered.length === 0 && (
            <div className={styles.noResults}>Sin resultados</div>
          )}
        </div>
      </div>
    );
  };

  if (availableCategories.length === 0) return null;

  return (
    <div className={styles.filterBar}>
      <div className={styles.filterControls}>
        <div className={styles.categoryButtons}>
          {availableCategories.map((cat) => {
            const isActive = openCategory === cat;
            const hasValues =
              cat === "fecha"
                ? !!(filters.fechaDesde || filters.fechaHasta)
                : (filters[cat] as string[]).length > 0;
            return (
              <button
                key={cat}
                ref={cat === openCategory ? buttonRef : undefined}
                type="button"
                className={`${styles.categoryBtn} ${isActive ? styles.categoryBtnActive : ""} ${hasValues ? styles.categoryBtnHasValues : ""}`}
                onClick={() => toggleCategory(cat)}
              >
                {CATEGORY_LABELS[cat]}
                {hasValues && <span className={styles.dot} />}
              </button>
            );
          })}
        </div>

        {activeCount > 0 && (
          <button type="button" className={styles.clearBtn} onClick={onClearAll}>
            Limpiar filtros
          </button>
        )}
      </div>

      {/* Active filter chips */}
      {chips.length > 0 && (
        <div className={styles.chipsRow}>
          {chips.map((chip, i) => (
            <span key={`${chip.key}-${chip.value}-${i}`} className={styles.chip}>
              <span className={styles.chipLabel}>{chip.label}:</span> {chip.value}
              <button
                type="button"
                className={styles.chipRemove}
                onClick={() => handleRemoveChip(chip)}
                aria-label={`Quitar filtro ${chip.label}: ${chip.value}`}
              >
                &times;
              </button>
            </span>
          ))}
        </div>
      )}

      {/* Popover */}
      {openCategory && (
        <div className={styles.popover} ref={popoverRef}>
          <div className={styles.popoverHeader}>
            {CATEGORY_LABELS[openCategory]}
          </div>
          {renderPopoverContent()}
        </div>
      )}
    </div>
  );
}
