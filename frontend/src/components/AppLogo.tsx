interface Props {
  size?: number;
  className?: string;
}

export default function AppLogo({ size = 28, className }: Props) {
  return (
    <img
      src="/logo.png"
      alt="Alertas Judiciales"
      width={size}
      height={size}
      className={className}
      style={{ objectFit: "contain" }}
    />
  );
}
