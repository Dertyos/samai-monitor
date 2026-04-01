import { API_URL } from "../config/auth";
import { getIdToken } from "./cognito";

async function authFetch(path: string, options: RequestInit = {}): Promise<Response> {
  const token = await getIdToken();
  const res = await fetch(`${API_URL}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
      ...options.headers,
    },
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.error || `HTTP ${res.status}`);
  }
  return res;
}

export interface RadicadoDTO {
  radicado: string;
  radicadoFormato: string;
  corporacion: string;
  alias: string;
  ultimoOrden: number;
  activo: boolean;
  fuente?: string;       // "samai" | "rama_judicial" | "siugj"
  idProceso?: number | null;
  fechaUltimaActuacion?: string;
  createdAt?: string;
  etiquetas?: string[];  // IDs de etiquetas asignadas
  // Metadata enriquecida para filtros
  despacho?: string;
  ciudad?: string;
  especialidad?: string;
  instancia?: string;
  vigente?: string;
  fechaInicioProceso?: string;
}

export interface EtiquetaDTO {
  etiquetaId: string;
  nombre: string;
  color: string;
  createdAt?: string;
}

export interface RJProcesoDTO {
  idProceso: number | null;  // null for SIUGJ results
  despacho: string;
  departamento: string;
  sujetosProcesales: string;
  fechaUltimaActuacion: string;
  llaveProceso: string;
  sistema: "cpnu" | "siugj";  // which backend system found this process
}

export interface AlertaDTO {
  sk: string;
  radicado: string;
  orden: number;
  nombreActuacion: string;
  fechaActuacion: string;
  anotacion: string;
  createdAt: string;
  leido: boolean;
}

export interface ActuacionDTO {
  orden: number;
  nombre: string;
  fecha: string;
  anotacion: string;
  estado: string;
  decision: string | null;
  docHash: string | null;
}

export interface ProcesoDTO {
  despacho: string;
  ponente: string;
  tipoProceso: string;
  claseActuacion: string;
  fechaUltimaActuacion: string;
}

export interface ParteDTO {
  nombre: string;
  tipo: string;
}

export interface DetalleDTO {
  proceso: ProcesoDTO;
  partes: ParteDTO[];
  actuaciones: ActuacionDTO[];
  corporacion?: string;
  fuente?: string;
  idProceso?: number;
}

export async function getRadicados(): Promise<RadicadoDTO[]> {
  const res = await authFetch("/radicados");
  return res.json();
}

export interface AddRadicadoMeta {
  despacho?: string;
  ciudad?: string;
}

export async function addRadicado(
  radicado: string,
  alias: string,
  fuente: string = "samai",
  idProceso?: number,
  meta?: AddRadicadoMeta,
): Promise<RadicadoDTO> {
  const body: Record<string, unknown> = { radicado, alias, fuente };
  if (idProceso !== undefined) body.id_proceso = idProceso;
  if (meta?.despacho) body.despacho = meta.despacho;
  if (meta?.ciudad) body.ciudad = meta.ciudad;
  const res = await authFetch("/radicados", {
    method: "POST",
    body: JSON.stringify(body),
  });
  return res.json();
}

export async function updateRadicadoAlias(
  radicado: string,
  alias: string,
): Promise<RadicadoDTO> {
  const res = await authFetch(`/radicados/${radicado}`, {
    method: "PATCH",
    body: JSON.stringify({ alias }),
  });
  return res.json();
}

export async function toggleRadicadoActivo(
  radicado: string,
): Promise<{ activo: boolean }> {
  const res = await authFetch(`/radicados/${radicado}/toggle`, { method: "PATCH" });
  return res.json();
}

export async function deleteRadicado(radicado: string): Promise<void> {
  await authFetch(`/radicados/${radicado}`, { method: "DELETE" });
}

export async function getHistorial(radicado: string): Promise<ActuacionDTO[]> {
  const res = await authFetch(`/radicados/${radicado}/historial`);
  return res.json();
}

export async function getAlertas(): Promise<AlertaDTO[]> {
  const res = await authFetch("/alertas");
  return res.json();
}

const SAMAI_BASE = "https://samaicore.consejodeestado.gov.co/api";

export function getDocumentoUrl(corporacion: string, radicado: string, docHash: string): string {
  return `${SAMAI_BASE}/DescargarProvidenciaPublica/${corporacion}/${radicado}/${docHash}/2`;
}

export async function getDetalle(radicado: string): Promise<DetalleDTO> {
  const res = await authFetch(`/radicados/${radicado}/detalle`);
  return res.json();
}

export async function markAllAlertasRead(): Promise<{ count: number }> {
  const res = await authFetch("/alertas/read-all", { method: "PATCH" });
  return res.json();
}

export async function markAlertaRead(sk: string): Promise<void> {
  await authFetch(`/alertas/${encodeURIComponent(sk)}/read`, { method: "PATCH" });
}

export async function buscarProceso(numProceso: string): Promise<unknown[]> {
  const res = await authFetch(`/buscar/${numProceso}`);
  return res.json();
}

export async function buscarRamaJudicial(numProceso: string): Promise<RJProcesoDTO[]> {
  const digits = numProceso.replace(/\D/g, "");
  const res = await authFetch(`/buscar-rj/${digits}`);
  return res.json();
}

// --- Etiquetas ---

export async function getEtiquetas(): Promise<EtiquetaDTO[]> {
  const res = await authFetch("/etiquetas");
  return res.json();
}

export async function createEtiqueta(
  nombre: string,
  color: string,
): Promise<EtiquetaDTO> {
  const res = await authFetch("/etiquetas", {
    method: "POST",
    body: JSON.stringify({ nombre, color }),
  });
  return res.json();
}

export async function updateEtiqueta(
  etiquetaId: string,
  nombre: string,
  color: string,
): Promise<EtiquetaDTO> {
  const res = await authFetch(`/etiquetas/${etiquetaId}`, {
    method: "PATCH",
    body: JSON.stringify({ nombre, color }),
  });
  return res.json();
}

export async function deleteEtiqueta(etiquetaId: string): Promise<void> {
  await authFetch(`/etiquetas/${etiquetaId}`, { method: "DELETE" });
}

export async function updateRadicadoEtiquetas(
  radicado: string,
  etiquetas: string[],
): Promise<{ etiquetas: string[] }> {
  const res = await authFetch(`/radicados/${radicado}/etiquetas`, {
    method: "PATCH",
    body: JSON.stringify({ etiquetas }),
  });
  return res.json();
}
