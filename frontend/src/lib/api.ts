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

export async function deleteCuenta(): Promise<void> {
  await authFetch("/cuenta", { method: "DELETE" });
}

// --- Billing ---

export interface BillingStatusDTO {
  plan: string;
  planName: string;
  processLimit: number;
  processCount: number;
}

export interface BillingPlanDTO {
  id: string;
  name: string;
  amount: number;
  currency: string;
  interval: string;
  trialDays: number;
  features: Record<string, unknown>;
}

export interface BillingSubscriptionDTO {
  planId: string;
  status: string;
  currentPeriodStart: string;
  currentPeriodEnd: string;
  cancelAtPeriodEnd: boolean;
}

export interface BillingInvoiceDTO {
  date: string;
  amount: number;
  status: string;
  transactionId: string;
  paymentMethod: string;
  reference: string;
}

export interface WompiConfigDTO {
  publicKey: string;
  sandbox: boolean;
}

export interface SubscribeResponseDTO {
  reference: string;
  amountInCents: number;
  currency: string;
  integrityHash: string;
  publicKey: string;
  planName: string;
}

export async function getBillingStatus(): Promise<BillingStatusDTO> {
  const res = await authFetch("/billing/status");
  return res.json();
}

export async function getBillingPlans(): Promise<BillingPlanDTO[]> {
  const res = await authFetch("/billing/plans");
  return res.json();
}

export async function getBillingSubscription(): Promise<{ subscription: BillingSubscriptionDTO | null }> {
  const res = await authFetch("/billing/subscription");
  return res.json();
}

export async function createSubscribeIntent(planId: string): Promise<SubscribeResponseDTO> {
  const res = await authFetch("/billing/subscribe", {
    method: "POST",
    body: JSON.stringify({ planId }),
  });
  return res.json();
}

export async function cancelSubscription(): Promise<{ message: string; refunded: boolean }> {
  const res = await authFetch("/billing/subscription", { method: "DELETE" });
  return res.json();
}

export interface UpgradeResponseDTO {
  upgraded: boolean;
  message?: string;
  reference?: string;
  amountInCents?: number;
  proratedAmount?: number;
  currency?: string;
  integrityHash?: string;
  publicKey?: string;
  newPlanName?: string;
  remainingDays?: number;
}

export async function upgradeSubscription(planId: string): Promise<UpgradeResponseDTO> {
  const res = await authFetch("/billing/upgrade", {
    method: "POST",
    body: JSON.stringify({ planId }),
  });
  return res.json();
}

export interface DowngradeResponseDTO {
  message: string;
  pendingPlanId: string;
  effectiveAt: string;
}

export async function downgradeSubscription(planId: string): Promise<DowngradeResponseDTO> {
  const res = await authFetch("/billing/downgrade", {
    method: "POST",
    body: JSON.stringify({ planId }),
  });
  return res.json();
}

export async function getBillingInvoices(): Promise<BillingInvoiceDTO[]> {
  const res = await authFetch("/billing/invoices");
  return res.json();
}

export async function getWompiConfig(): Promise<WompiConfigDTO> {
  const res = await authFetch("/billing/wompi-config");
  return res.json();
}

// --- Teams ---

export interface PendingInvitationDTO {
  email: string;
  inviteId: string;
  status: string;
  createdAt: string;
}

export interface TeamDTO {
  teamId: string;
  name: string;
  ownerUserId: string;
  planId: string;
  createdAt: string;
  active: boolean;
  pendingConfirmation: boolean;
  processLimit: number;
  processCount: number;
  members: TeamMemberDTO[];
  pendingInvitations: PendingInvitationDTO[];
}

export interface TeamMemberDTO {
  teamId: string;
  userId: string;
  email: string;
  role: "owner" | "member";
  joinedAt: string;
}

export async function getTeams(): Promise<TeamDTO[]> {
  const res = await authFetch("/teams");
  return res.json();
}

export async function createTeam(name: string): Promise<TeamDTO> {
  const res = await authFetch("/teams", {
    method: "POST",
    body: JSON.stringify({ name }),
  });
  return res.json();
}

export async function addTeamMember(teamId: string, email: string): Promise<TeamMemberDTO & { added?: boolean; invited?: boolean; email?: string; message?: string }> {
  const res = await authFetch(`/teams/${teamId}/members`, {
    method: "POST",
    body: JSON.stringify({ email }),
  });
  return res.json();
}

export async function removeTeamMember(teamId: string, userId: string): Promise<void> {
  await authFetch(`/teams/${teamId}/members/${userId}`, { method: "DELETE" });
}

export async function revokeInvitation(inviteId: string): Promise<void> {
  await authFetch(`/invitations/${inviteId}`, { method: "DELETE" });
}

export async function confirmTeam(teamId: string): Promise<{ status: string; membersReactivated: number }> {
  const res = await authFetch(`/teams/${teamId}/confirm`, { method: "POST" });
  return res.json();
}

// --- Alert Schedules ---

export interface AlertScheduleDTO {
  alertHourCot: number;
  alertHourUtc: number;
  createdAt: string;
  updatedAt: string;
}

export interface AlertScheduleResponseDTO {
  schedule: AlertScheduleDTO | null;
  eligible: boolean;
}

export async function getAlertSchedule(): Promise<AlertScheduleResponseDTO> {
  const res = await authFetch("/alert-schedule");
  return res.json();
}

export async function putAlertSchedule(hourCot: number): Promise<{ schedule: AlertScheduleDTO }> {
  const res = await authFetch("/alert-schedule", {
    method: "PUT",
    body: JSON.stringify({ hourCot }),
  });
  return res.json();
}

export async function deleteAlertSchedule(): Promise<void> {
  await authFetch("/alert-schedule", { method: "DELETE" });
}

