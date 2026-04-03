import { useState, useCallback } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  getBillingStatus,
  getBillingSubscription,
  getBillingInvoices,
  createSubscribeIntent,
  cancelSubscription,
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
            <td>{new Date(inv.date).toLocaleDateString("es-CO")}</td>
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

  const status = statusQuery.data;
  const sub = subQuery.data?.subscription;
  const isFreePlan = !sub || status?.plan === "plan-gratuito";

  const handleSubscribe = useCallback(async (planId: string) => {
    try {
      const intent = await subscribeMutation.mutateAsync(planId);

      // Cargar widget de Wompi
      if (!window.WidgetCheckout) {
        // Cargar script dinamicamente si no esta
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
          // Refrescar datos despues de un momento (webhook puede tardar)
          setTimeout(() => {
            queryClient.invalidateQueries({ queryKey: ["billing-status"] });
            queryClient.invalidateQueries({ queryKey: ["billing-subscription"] });
            queryClient.invalidateQueries({ queryKey: ["billing-invoices"] });
          }, 5000);
        }
      });
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Error al iniciar pago");
    }
  }, [subscribeMutation, queryClient, toast]);

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
              {isFreePlan ? (
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
          message="Tu plan seguira activo hasta el final del periodo de facturacion. Despues de eso, volveras al plan gratuito (5 procesos). Tus procesos existentes no se eliminaran."
          confirmLabel="Si, cancelar"
          onConfirm={() => cancelMutation.mutate()}
          onCancel={() => setShowCancel(false)}
        />
      )}
    </div>
  );
}
