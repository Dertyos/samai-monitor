/** Formatea un radicado de 23 dígitos a formato legible con guiones. */
export function formatRadicado(raw: string): string {
  const d = raw.replace(/\D/g, "");
  if (d.length !== 23) return raw;
  return `${d.slice(0, 5)}-${d.slice(5, 7)}-${d.slice(7, 9)}-${d.slice(9, 12)}-${d.slice(12, 16)}-${d.slice(16, 21)}-${d.slice(21, 23)}`;
}

/** Formatea una fecha ISO o SAMAI a formato legible DD/MM/YYYY. */
export function formatDate(raw: string): string {
  if (!raw) return "";
  const trimmed = raw.trim();
  // ISO format: YYYY-MM-DD...
  if (/^\d{4}-\d{2}-\d{2}/.test(trimmed)) {
    const [y, m, day] = trimmed.slice(0, 10).split("-");
    return `${day}/${m}/${y}`;
  }
  // Fallback: parse with Date (handles "Mar 31 2020 4:31PM" etc.)
  const d = new Date(trimmed);
  if (isNaN(d.getTime())) return trimmed;
  const day = String(d.getDate()).padStart(2, "0");
  const m = String(d.getMonth() + 1).padStart(2, "0");
  const y = d.getFullYear();
  return `${day}/${m}/${y}`;
}

/** Decodifica entidades HTML (&#233; → é, etc). */
export function decodeHtml(text: string): string {
  if (!text) return "";
  const el = document.createElement("textarea");
  el.innerHTML = text;
  return el.value;
}

/** Tiempo relativo desde una fecha ISO. */
export function timeAgo(iso: string): string {
  if (!iso) return "";
  const now = Date.now();
  const then = new Date(iso).getTime();
  const diff = now - then;
  const mins = Math.floor(diff / 60000);
  if (mins < 60) return `hace ${mins}m`;
  const hours = Math.floor(mins / 60);
  if (hours < 24) return `hace ${hours}h`;
  const days = Math.floor(hours / 24);
  if (days < 30) return `hace ${days}d`;
  return formatDate(iso);
}
