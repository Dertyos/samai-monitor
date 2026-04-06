import { useState, useCallback } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  getBillingStatus,
  getBillingSubscription,
  getBillingInvoices,
  createSubscribeIntent,
  cancelSubscription,
  upgradeSubscription,
  downgradeSubscription,
  type BillingInvoiceDTO,
} from "../lib/api";
import { useTheme } from "../hooks/useTheme";
import { useToast } from "../hooks/useToast";
import AppLogo from "../components/AppLogo";
import ConfirmModal from "../components/ConfirmModal";
import s from "./Billing.module.css";

declare global {
  interface Window {
    WidgetCheckout: new (config: Record<string, unknown>) => {
      open: (cb: (result: { transaction: { id: string } }) => void) => void;
    };
  }
}

function formatCOP(amount: number): string {
  return `$${amount.toLocaleString("es-CO")}`;
}

function InvoicesList({ invoices }: { invoices: BillingInvoiceDTO[] }) {
  if (invoices.length === 0) {
    return <p className={s.emptyInvoices}>No hay pagos registrados aun.</p>;
  }
  return (
    <table className={s.invoicesTable}>
      <thead>
        <tr>
          <th>Fecha</th>
          <th>Monto</th>
          <th>Metodo</th>
          <th>ID Transaccion</th>
        </tr>
      </thead>
      <tbody>
        {invoices.map((inv) => (
          <tr key={inv.transactionId}>
            <td>{new Date(inv.date).toLocaleString("es-CO", { dateStyle: "short", timeStyle: "short" })}</td>
            <td>{formatCOP(inv.amount)}</td>
            <td>{inv.paymentMethod}</td>
            <td className={s.ref}>{inv.transactionId}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

export default function Billing() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const selectedPlan = searchParams.get("plan") ?? "";
  const { theme, toggle: toggleTheme } = useTheme();
  const toast = useToast();
  const queryClient = useQueryClient();
  const [showCancel, setShowCancel] = useState(false);

  const statusQuery = useQuery({
    queryKey: ["billing-status"],
    queryFn: getBillingStatus,
  });

  const subQuery = useQuery({
    queryKey: ["billing-subscription"],
    queryFn: getBillingSubscription,
  });

  const invoicesQuery = useQuery({
    queryKey: ["billing-invoices"],
    queryFn: getBillingInvoices,
  });

  const cancelMutation = useMutation({
    mutationFn: cancelSubscription,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["billing-status"] });
      queryClient.invalidateQueries({ queryKey: ["billing-subscription"] });
      toast.success("Suscripcion cancelada");
      setShowCancel(false);
    },
    onError: (err: Error) => toast.error(err.message),
  });

  const subscribeMutation = useMutation({
    mutationFn: createSubscribeIntent,
  });

  const downgradeMutation = useMutation({
    mutationFn: (planId: string) => downgradeSubscription(planId),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ["billing-status"] });
      queryClient.invalidateQueries({ queryKey: ["billing-subscription"] });
      toast.success(data.message);
    },
    onError: (err: Error) => toast.error(err.message),
  });

  const status = statusQuery.data;
  const sub = subQuery.data?.subscription;
  const isInTeam = !!(status as Record<string, unknown>)?.teamId;
  const isFreePlan = !isInTeam && (!sub || status?.plan === "plan-gratuito");

  const PLAN_RANK: Record<string, number> = {
    "plan-gratuito": 0, "plan-pro": 1, "plan-pro-plus": 2, "plan-firma": 3, "plan-enterprise": 4,
  };

  const openWompiWidget = useCallback(async (intent: { amountInCents: number; reference: string; publicKey: string; integrityHash: string }) => {
    if (!window.WidgetCheckout) {
      await new Promise<void>((resolve, reject) => {
        const script = document.createElement("script");
        script.src = "https://checkout.wompi.co/widget.js";
        script.onload = () => resolve();
        script.onerror = () => reject(new Error("Error cargando Wompi"));
        document.head.appendChild(script);
      });
    }

    const checkout = new window.WidgetCheckout({
      currency: "COP",
      amountInCents: intent.amountInCents,
      reference: intent.reference,
      publicKey: intent.publicKey,
      "signature:integrity": intent.integrityHash,
      redirectUrl: `${window.location.origin}/billing`,
    });

    checkout.open((result) => {
      if (result?.transaction?.id) {
        toast.success("Pago procesado. Tu suscripcion se activara en unos segundos.");
        setTimeout(() => {
          queryClient.invalidateQueries({ queryKey: ["billing-status"] });
          queryClient.invalidateQueries({ queryKey: ["billing-subscription"] });
          queryClient.invalidateQueries({ queryKey: ["billing-invoices"] });
        }, 5000);
      }
    });
  }, [queryClient, toast]);

  const handleSubscribe = useCallback(async (planId: string) => {
    try {
      const currentRank = PLAN_RANK[status?.plan ?? "plan-gratuito"] ?? 0;
      const targetRank = PLAN_RANK[planId] ?? 0;

      if (!isFreePlan && targetRank > currentRank) {
        // Upgrade: cobrar diferencia prorrateada
        const upgradeResp = await upgradeSubscription(planId);
        if (upgradeResp.upgraded) {
          // Upgrade sin cobro (diferencia minima)
          toast.success(upgradeResp.message ?? "Upgrade completado");
          queryClient.invalidateQueries({ queryKey: ["billing-status"] });
          queryClient.invalidateQueries({ queryKey: ["billing-subscription"] });
          return;
        }
        // Abrir Wompi con monto prorrateado
        await openWompiWidget({
          amountInCents: upgradeResp.amountInCents!,
          reference: upgradeResp.reference!,
          publicKey: upgradeResp.publicKey!,
          integrityHash: upgradeResp.integrityHash!,
        });
        return;
      }

      if (!isFreePlan && targetRank < currentRank && targetRank > 0) {
        // Downgrade: programar al fin del periodo
        downgradeMutation.mutate(planId);
        return;
      }

      // Nueva suscripcion (desde gratuito)
      const intent = await subscribeMutation.mutateAsync(planId);
      await openWompiWidget(intent);
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Error al procesar");
    }
  }, [subscribeMutation, downgradeMutation, queryClient, toast, status, isFreePlan, openWompiWidget, PLAN_RANK]);

  return (
    <div className={s.page}>
      <nav className={s.nav}>
        <div className={s.navInner}>
          <div className={s.navBrand} onClick={() => navigate("/")}>
            <AppLogo size={28} />
            <span className={s.navTitle}>Alertas Judiciales</span>
          </div>
          <div className={s.navLinks}>
            <button className={s.themeBtn} onClick={toggleTheme} title="Cambiar tema">
              {theme === "dark" ? "\u2600\ufe0f" : "\ud83c\udf19"}
            </button>
            <button className="btn btn-secondary btn-sm" onClick={() => navigate("/dashboard")}>
              Dashboard
            </button>
          </div>
        </div>
      </nav>

      <div className={s.container}>
        <h1 className={s.title}>Mi suscripcion</h1>

        {/* Current plan status */}
        {status && (
          <div className={s.statusCard}>
            <div className={s.statusHeader}>
              <div>
                <span className={s.planLabel}>Plan actual</span>
                <h2 className={s.planName}>{status.planName}</h2>
              </div>
              <div className={s.usage}>
                <span className={s.usageCount}>{status.processCount}/{status.processLimit}</span>
                <span className={s.usageLabel}>procesos</span>
                <div className={s.usageBar}>
                  <div
                    className={s.usageFill}
                    style={{ width: `${Math.min(100, (status.processCount / status.processLimit) * 100)}%` }}
                  />
                </div>
              </div>
            </div>

            {sub && (
              <div className={s.subDetails}>
                <p>Estado: <strong>{sub.status}</strong></p>
                {sub.currentPeriodEnd && (
                  <p>Proximo cobro: <strong>{new Date(sub.currentPeriodEnd).toLocaleDateString("es-CO")}</strong></p>
                )}
                {sub.cancelAtPeriodEnd && (
                  <p className={s.cancelNotice}>Se cancelara al final del periodo actual.</p>
                )}
              </div>
            )}

            <div className={s.actions}>
              {isInTeam ? (
                <p style={{ fontSize: "0.85rem", color: "var(--text-secondary)" }}>
                  Estas cubierto por el equipo <strong>{(status as Record<string, unknown>)?.teamName as string}</strong>.
                  No necesitas suscripcion personal.
                </p>
              ) : isFreePlan ? (
                <>
                  <button
                    className="btn btn-primary"
                    onClick={() => handleSubscribe(selectedPlan || "plan-pro")}
                    disabled={subscribeMutation.isPending}
                  >
                    {subscribeMutation.isPending ? "Procesando..." : "Upgrade a Pro — $19,900/mes"}
                  </button>
                  <button className="btn btn-secondary" onClick={() => navigate("/planes")}>
                    Ver todos los planes
                  </button>
                </>
              ) : (
                <>
                  {selectedPlan && selectedPlan !== status?.plan && (
                    <button
                      className="btn btn-primary"
                      onClick={() => handleSubscribe(selectedPlan)}
                      disabled={subscribeMutation.isPending || downgradeMutation.isPending}
                    >
                      {(PLAN_RANK[selectedPlan] ?? 0) > (PLAN_RANK[status?.plan ?? ""] ?? 0)
                        ? "Confirmar upgrade"
                        : "Confirmar downgrade"
                      }
                    </button>
                  )}
                  <button className="btn btn-secondary" onClick={() => navigate("/planes")}>
                    Cambiar plan
                  </button>
                  <button className="btn btn-danger" onClick={() => setShowCancel(true)}>
                    Cancelar suscripcion
                  </button>
                </>
              )}
            </div>

            <p className={s.secure}>
              Pago seguro procesado por Wompi (Bancolombia). Acepta tarjetas, PSE, Nequi y mas.
            </p>
          </div>
        )}

        {/* Invoices */}
        <section className={s.invoicesSection}>
          <h2>Historial de pagos</h2>
          {invoicesQuery.isLoading ? (
            <p className={s.loading}>Cargando...</p>
          ) : (
            <InvoicesList invoices={invoicesQuery.data ?? []} />
          )}
        </section>
      </div>

      {showCancel && (
        <ConfirmModal
          title="Cancelar suscripcion"
          message="Si pagaste hace menos de 24 horas con tarjeta, se intentara el reembolso automatico. De lo contrario, tu plan seguira activo hasta el final del periodo. Despues, volveras al plan gratuito (5 procesos)."
          confirmLabel="Si, cancelar"
          onConfirm={() => cancelMutation.mutate()}
          onCancel={() => setShowCancel(false)}
        />
      )}
    </div>
  );
}
