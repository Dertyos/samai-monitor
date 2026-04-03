import { useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { useAuth } from "../hooks/useAuth";
import { useTheme } from "../hooks/useTheme";
import { getBillingPlans, getBillingStatus, type BillingPlanDTO } from "../lib/api";
import AppLogo from "../components/AppLogo";
import s from "./Planes.module.css";

const PLAN_ORDER = ["plan-gratuito", "plan-pro", "plan-pro-plus", "plan-firma", "plan-enterprise"];

function formatCOP(amount: number): string {
  if (amount === 0) return "Gratis";
  return `$${amount.toLocaleString("es-CO")}`;
}

const FEATURE_LABELS: Record<string, string> = {
  max_processes: "Procesos monitoreados",
  max_users: "Usuarios",
  alertas_email: "Alertas por email",
  alertas_push: "Notificaciones push",
  alertas_whatsapp: "Alertas WhatsApp",
  frecuencia_personalizable: "Frecuencia personalizable",
  reportes_avanzados: "Reportes avanzados",
  soporte_prioritario: "Soporte prioritario",
  api_access: "Acceso API",
  integraciones: "Integraciones",
  account_manager: "Account manager",
  historial: "Historial de actuaciones",
  etiquetas: "Etiquetas personalizadas",
  exportacion_csv: "Exportacion CSV",
  busqueda_samai: "Busqueda SAMAI",
};

function PlanCard({
  plan,
  isCurrentPlan,
  isPopular,
  isAuthenticated,
  onSelect,
}: {
  plan: BillingPlanDTO;
  isCurrentPlan: boolean;
  isPopular: boolean;
  isAuthenticated: boolean;
  onSelect: () => void;
}) {
  const features = plan.features as Record<string, unknown>;
  return (
    <div className={`${s.card} ${isPopular ? s.popular : ""} ${isCurrentPlan ? s.current : ""}`}>
      {isPopular && <div className={s.badge}>Mas popular</div>}
      {isCurrentPlan && <div className={s.badgeCurrent}>Tu plan</div>}
      <h3 className={s.planName}>{plan.name}</h3>
      <div className={s.price}>
        <span className={s.amount}>{formatCOP(plan.amount)}</span>
        {plan.amount > 0 && <span className={s.interval}>/mes</span>}
      </div>
      {plan.trialDays > 0 && (
        <p className={s.trial}>{plan.trialDays} dias de prueba gratis</p>
      )}
      <ul className={s.features}>
        {Object.entries(features).map(([key, val]) => {
          if (val === false) return null;
          const label = FEATURE_LABELS[key] || key;
          const display = typeof val === "number" ? `${val} ${label.toLowerCase()}` : label;
          return (
            <li key={key} className={s.feature}>
              <span className={s.check}>&#10003;</span>
              {display}
            </li>
          );
        })}
      </ul>
      <button
        className={`${s.cta} ${isCurrentPlan ? s.ctaDisabled : ""}`}
        onClick={onSelect}
        disabled={isCurrentPlan}
      >
        {isCurrentPlan
          ? "Plan actual"
          : plan.amount === 0
            ? "Empezar gratis"
            : isAuthenticated
              ? "Suscribirse"
              : "Empezar"}
      </button>
    </div>
  );
}

export default function Planes() {
  const navigate = useNavigate();
  const { isAuthenticated } = useAuth();
  const { theme, toggle: toggleTheme } = useTheme();

  const plansQuery = useQuery({
    queryKey: ["billing-plans"],
    queryFn: getBillingPlans,
    enabled: isAuthenticated,
  });

  const statusQuery = useQuery({
    queryKey: ["billing-status"],
    queryFn: getBillingStatus,
    enabled: isAuthenticated,
  });

  // Planes estáticos para usuarios no autenticados
  const staticPlans: BillingPlanDTO[] = [
    { id: "plan-gratuito", name: "Gratuito", amount: 0, currency: "cop", interval: "month", trialDays: 0, features: { max_processes: 5, alertas_email: true, historial: true, etiquetas: true, exportacion_csv: true, busqueda_samai: true } },
    { id: "plan-pro", name: "Pro", amount: 19900, currency: "cop", interval: "month", trialDays: 7, features: { max_processes: 25, alertas_email: true, alertas_push: true, frecuencia_personalizable: true, historial: true, etiquetas: true, exportacion_csv: true, busqueda_samai: true } },
    { id: "plan-pro-plus", name: "Pro +", amount: 59900, currency: "cop", interval: "month", trialDays: 7, features: { max_processes: 70, alertas_email: true, alertas_push: true, frecuencia_personalizable: true, historial: true, etiquetas: true, exportacion_csv: true, busqueda_samai: true } },
    { id: "plan-firma", name: "Firma", amount: 79900, currency: "cop", interval: "month", trialDays: 7, features: { max_processes: 150, max_users: 5, alertas_email: true, alertas_push: true, reportes_avanzados: true, soporte_prioritario: true, historial: true, etiquetas: true, exportacion_csv: true, busqueda_samai: true } },
    { id: "plan-enterprise", name: "Enterprise", amount: 249900, currency: "cop", interval: "month", trialDays: 14, features: { max_processes: 1000, max_users: 20, alertas_email: true, alertas_push: true, alertas_whatsapp: true, api_access: true, integraciones: true, account_manager: true, reportes_avanzados: true, soporte_prioritario: true, historial: true, etiquetas: true, exportacion_csv: true, busqueda_samai: true } },
  ];

  const plans = (plansQuery.data ?? staticPlans).sort((a, b) => {
    const ia = PLAN_ORDER.indexOf(a.id);
    const ib = PLAN_ORDER.indexOf(b.id);
    return ia - ib;
  });

  const currentPlan = statusQuery.data?.plan ?? "plan-gratuito";

  const handleSelect = (plan: BillingPlanDTO) => {
    if (!isAuthenticated) {
      navigate("/login");
      return;
    }
    if (plan.amount === 0) {
      navigate("/dashboard");
      return;
    }
    navigate(`/billing?plan=${plan.id}`);
  };

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
            {isAuthenticated ? (
              <button className="btn btn-primary btn-sm" onClick={() => navigate("/dashboard")}>
                Dashboard
              </button>
            ) : (
              <button className="btn btn-primary btn-sm" onClick={() => navigate("/login")}>
                Iniciar sesion
              </button>
            )}
          </div>
        </div>
      </nav>

      <header className={s.header}>
        <h1 className={s.title}>Planes y precios</h1>
        <p className={s.subtitle}>
          Monitoreo automatico de procesos judiciales en SAMAI.
          Empieza gratis, escala cuando lo necesites.
        </p>
      </header>

      <section className={s.grid}>
        {plans.map((plan) => (
          <PlanCard
            key={plan.id}
            plan={plan}
            isCurrentPlan={plan.id === currentPlan}
            isPopular={plan.id === "plan-pro"}
            isAuthenticated={isAuthenticated}
            onSelect={() => handleSelect(plan)}
          />
        ))}
      </section>

      <section className={s.comparison}>
        <h2>Comparacion con la competencia</h2>
        <table className={s.compTable}>
          <thead>
            <tr>
              <th>Procesos</th>
              <th>Alertas Judiciales</th>
              <th>Monolegal</th>
              <th>PleGlex</th>
            </tr>
          </thead>
          <tbody>
            <tr><td>5</td><td className={s.ours}>$0 (gratis)</td><td>$6,675</td><td>$5,000</td></tr>
            <tr><td>20</td><td className={s.ours}>$19,900</td><td>$26,700</td><td>$20,000</td></tr>
            <tr><td>50</td><td className={s.ours}>$79,900</td><td>$66,750</td><td>$50,000</td></tr>
            <tr><td>100</td><td className={s.ours}>$79,900</td><td>$133,500</td><td>$100,000</td></tr>
            <tr><td>500</td><td className={s.ours}>$249,900</td><td>$667,500</td><td>$500,000</td></tr>
          </tbody>
        </table>
        <p className={s.compNote}>Precios en COP/mes. Competidores cobran por proceso.</p>
      </section>

      <footer className={s.footer}>
        <p>&copy; {new Date().getFullYear()} Dertyos. Todos los derechos reservados.</p>
      </footer>
    </div>
  );
}
