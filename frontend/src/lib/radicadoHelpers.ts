/**
 * Mapa de códigos de especialidad judicial colombiana.
 * Dígitos 5-6 del radicado (23 dígitos sin guiones).
 */
const ESPECIALIDADES: Record<string, string> = {
  "01": "Civil",
  "02": "Familia",
  "03": "Agrario",
  "04": "Penal",
  "05": "Laboral",
  "06": "Penal Adolescentes",
  "07": "Promiscuo",
  "08": "Ejecucion de Penas",
  "09": "Penal Militar",
  "10": "Civil-Familia",
  "11": "Civil Municipal",
  "12": "Pequenas Causas",
  "20": "Constitucional",
  "23": "Contencioso Administrativo",
  "31": "Penal Municipal",
  "33": "Administrativo",
  "40": "Constitucional",
  "41": "Disciplinario",
  "44": "Jurisdiccion Especial de Paz",
  "50": "Restitucion de Tierras",
};

/** Extrae la especialidad judicial del radicado (dígitos 5-6). */
export function getEspecialidad(radicado: string): string {
  const digits = radicado.replace(/\D/g, "");
  if (digits.length < 7) return "";
  const code = digits.slice(5, 7);
  return ESPECIALIDADES[code] || `Especialidad ${code}`;
}

/**
 * Extrae la instancia del radicado (dígitos 21-22).
 * "00" = Primera Instancia, "01" = Segunda Instancia, "02" = Casacion, etc.
 */
const INSTANCIAS: Record<string, string> = {
  "00": "Primera Instancia",
  "01": "Segunda Instancia",
  "02": "Casacion",
};

export function getInstancia(radicado: string): string {
  const digits = radicado.replace(/\D/g, "");
  if (digits.length < 23) return "";
  const code = digits.slice(21, 23);
  return INSTANCIAS[code] || `Instancia ${code}`;
}
