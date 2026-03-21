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
}

export async function getRadicados(): Promise<RadicadoDTO[]> {
  const res = await authFetch("/radicados");
  return res.json();
}

export async function addRadicado(
  radicado: string,
  alias: string
): Promise<RadicadoDTO> {
  const res = await authFetch("/radicados", {
    method: "POST",
    body: JSON.stringify({ radicado, alias }),
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

export async function getDetalle(radicado: string): Promise<DetalleDTO> {
  const res = await authFetch(`/radicados/${radicado}/detalle`);
  return res.json();
}

export async function markAlertaRead(sk: string): Promise<void> {
  await authFetch(`/alertas/${encodeURIComponent(sk)}/read`, { method: "PATCH" });
}

export async function buscarProceso(numProceso: string): Promise<unknown[]> {
  const res = await authFetch(`/buscar/${numProceso}`);
  return res.json();
}
