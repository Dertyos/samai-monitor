import styles from "./Skeleton.module.css";

/**
 * Skeleton — placeholder animado para contenido en carga.
 *
 * Reutilizable: ajusta width/height via props.
 * Usa animación shimmer CSS para indicar carga.
 */
export function Skeleton({
  width = "100%",
  height = "1rem",
  borderRadius = "4px",
}: {
  width?: string;
  height?: string;
  borderRadius?: string;
}) {
  return (
    <div
      className={styles.skeleton}
      style={{ width, height, borderRadius }}
    />
  );
}

/** Skeleton de una tarjeta RadicadoCard. */
export function RadicadoCardSkeleton() {
  return (
    <div className={styles.card}>
      <Skeleton width="60%" height="1rem" />
      <Skeleton width="40%" height="0.8rem" />
      <div className={styles.row}>
        <Skeleton width="120px" height="0.8rem" />
        <Skeleton width="50px" height="1.2rem" borderRadius="12px" />
      </div>
      <Skeleton width="80px" height="1.8rem" borderRadius="6px" />
    </div>
  );
}

/** Skeleton de la stats bar. */
export function StatsBarSkeleton() {
  return (
    <div className={styles.statsBar}>
      {[0, 1, 2, 3].map((i) => (
        <div key={i} className={styles.statSkeleton}>
          <Skeleton width="2rem" height="1.5rem" />
          <Skeleton width="4rem" height="0.6rem" />
        </div>
      ))}
    </div>
  );
}
