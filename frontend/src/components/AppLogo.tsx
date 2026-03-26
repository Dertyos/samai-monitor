/**
 * AppLogo — Logotipo SVG de la app.
 *
 * Campana estilizada con escudo/balanza judicial.
 * Sin texto — el texto va en el componente padre.
 */
interface Props {
  size?: number;
  className?: string;
}

export default function AppLogo({ size = 28, className }: Props) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 32 32"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      aria-hidden="true"
      className={className}
    >
      {/* Fondo redondeado */}
      <rect width="32" height="32" rx="8" fill="var(--primary)" />

      {/* Campana */}
      <path
        d="M16 7C13.24 7 11 9.24 11 12v5l-1.5 1.5V20h13v-1.5L21 17v-5c0-2.76-2.24-5-5-5z"
        fill="white"
        opacity="0.95"
      />
      {/* Base campana */}
      <path
        d="M14.5 20.5a1.5 1.5 0 003 0"
        stroke="white"
        strokeWidth="1.5"
        strokeLinecap="round"
        fill="none"
      />
      {/* Linea balanza */}
      <line x1="11" y1="14" x2="21" y2="14" stroke="var(--primary)" strokeWidth="1.2" opacity="0.6" />
    </svg>
  );
}
