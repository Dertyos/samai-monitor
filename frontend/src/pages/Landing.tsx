import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useTheme } from "../hooks/useTheme";
import { useAuth } from "../hooks/useAuth";
import AppLogo from "../components/AppLogo";
import s from "./Landing.module.css";

/* ── Scroll reveal — un solo IntersectionObserver compartido ── */
const revealObserver = (() => {
  if (typeof window === "undefined") return null;
  return new IntersectionObserver(
    (entries) => {
      for (const entry of entries) {
        if (entry.isIntersecting) {
          (entry.target as HTMLElement).classList.add(s.visible);
          revealObserver!.unobserve(entry.target);
        }
      }
    },
    { threshold: 0.15 },
  );
})();

function RevealSection({
  children,
  className = "",
  delay = 0,
}: {
  children: React.ReactNode;
  className?: string;
  delay?: number;
}) {
  const ref = useRef<HTMLDivElement>(null);
  useEffect(() => {
    const el = ref.current;
    if (!el || !revealObserver) return;
    revealObserver.observe(el);
    return () => revealObserver.unobserve(el);
  }, []);
  return (
    <div
      ref={ref}
      className={`${s.reveal} ${className}`}
      style={delay ? { transitionDelay: `${delay}ms` } : undefined}
    >
      {children}
    </div>
  );
}

/* ── FAQ Accordion item ── */
function FaqItem({ q, a }: { q: string; a: string }) {
  const [open, setOpen] = useState(false);
  return (
    <div className={`${s.faqItem} ${open ? s.faqOpen : ""}`}>
      <button
        className={s.faqQuestion}
        onClick={() => setOpen(!open)}
        aria-expanded={open}
      >
        <span>{q}</span>
        <span className={s.faqChevron}>{open ? "\u2212" : "+"}</span>
      </button>
      <div className={s.faqAnswer} aria-hidden={!open}>
        <p>{a}</p>
      </div>
    </div>
  );
}

/* ── Data ── */
const FEATURES = [
  {
    icon: "\u{1F514}",
    title: "Alertas diarias",
    desc: "Recibe un email cada manana con las nuevas actuaciones de tus procesos. Nunca vuelvas a revisar SAMAI manualmente.",
    span: "wide",
  },
  {
    icon: "\u{1F50D}",
    title: "Busqueda inteligente",
    desc: "Busca por radicado en SAMAI y Rama Judicial desde un solo lugar.",
    span: "normal",
  },
  {
    icon: "\u{1F517}",
    title: "Acceso directo",
    desc: "Facilitamos el acceso a las plataformas de SAMAI y Rama Judicial para revisar los casos fácilmente.",
    span: "normal",
  },
  {
    icon: "\u{1F3F7}\uFE0F",
    title: "Etiquetas y filtros",
    desc: "Organiza tus procesos con etiquetas de colores. Filtra por estado, despacho, ciudad o alias.",
    span: "normal",
  },
  {
    icon: "\u{1F4CA}",
    title: "Timeline completo",
    desc: "Historial de todas las actuaciones con fechas, anotaciones y documentos. Exporta a CSV.",
    span: "normal",
  },
  {
    icon: "\u{1F319}",
    title: "Dark mode",
    desc: "Interfaz moderna con tema claro y oscuro. Tu vista te lo agradece.",
    span: "wide",
  },
];

const PLANS = [
  {
    name: "Gratis",
    price: "$0",
    period: "para siempre",
    processes: "5 procesos",
    features: [
      "Alertas diarias por email",
      "Dashboard completo",
      "Historial de actuaciones",
      "Etiquetas y filtros",
      "Exportacion CSV",
    ],
    cta: "Comenzar gratis",
    highlighted: false,
  },
  {
    name: "Pro",
    price: "$29.900",
    period: "COP/mes",
    processes: "30 procesos",
    features: [
      "Todo lo del plan Gratis",
      "Push notifications",
      "Alertas configurables",
      "Frecuencia personalizable",
      "Soporte por email",
    ],
    cta: "Empezar con Pro",
    highlighted: true,
  },
  {
    name: "Firma",
    price: "$79.900",
    period: "COP/mes",
    processes: "150 procesos",
    features: [
      "Todo lo de Pro",
      "Hasta 5 usuarios",
      "Reportes avanzados",
      "Soporte prioritario",
      "Multi-jurisdiccion",
    ],
    cta: "Empezar con Firma",
    highlighted: false,
  },
  {
    name: "Corporativo",
    price: "$249.900",
    period: "COP/mes",
    processes: "1.000 procesos",
    features: [
      "Todo lo de Firma",
      "Hasta 20 usuarios",
      "API & webhooks",
      "Account manager",
      "Integraciones custom",
    ],
    cta: "Contactar ventas",
    highlighted: false,
  },
];

const FAQS = [
  {
    q: "\u00bfEs seguro?",
    a: "Si. Consultamos unicamente fuentes publicas oficiales. Tu cuenta esta protegida con autenticacion segura y cifrado de extremo a extremo. Los datos judiciales son publicos por ley.",
  },
  {
    q: "\u00bfNecesito tarjeta de credito para el plan gratis?",
    a: "No. El plan gratis es 100% gratis, para siempre. Sin tarjeta, sin trampa.",
  },
  {
    q: "\u00bfQue pasa si supero el limite de procesos?",
    a: "Tus procesos existentes siguen monitoreandose. Solo se bloquea agregar nuevos hasta que hagas upgrade o liberes espacio.",
  },
  {
    q: "\u00bfPuedo cancelar cuando quiera?",
    a: "Si. Sin contratos, sin permanencia. Cancelas y tu cuenta vuelve al plan gratis automaticamente.",
  },
  {
    q: "\u00bfCubren Rama Judicial y otras plataformas?",
    a: "Si. Ademas de SAMAI (contencioso-administrativo), ya soportamos consultas en la Rama Judicial. Seguimos integrando mas fuentes.",
  },
  {
    q: "\u00bfCuantas veces al dia se revisan los procesos?",
    a: "Actualmente una vez al dia, a las 7 AM hora Colombia. Planes pagos tendran frecuencia configurable.",
  },
];

/* ── Main component ── */
export default function Landing() {
  const navigate = useNavigate();
  const { theme, toggle: toggleTheme } = useTheme();
  const { isAuthenticated } = useAuth();
  const [navScrolled, setNavScrolled] = useState(false);

  useEffect(() => {
    const onScroll = () => setNavScrolled(window.scrollY > 20);
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  const goSignup = () => {
    if (isAuthenticated) {
      navigate("/dashboard");
    } else {
      navigate("/login?mode=register");
    }
  };

  const goLogin = () => {
    if (isAuthenticated) {
      navigate("/dashboard");
    } else {
      navigate("/login");
    }
  };

  return (
    <div className={s.page}>
      {/* ── Nav ── */}
      <nav className={`${s.nav} ${navScrolled ? s.navScrolled : ""}`}>
        <div className={s.navInner}>
          <div className={s.navBrand} onClick={() => window.scrollTo({ top: 0, behavior: "smooth" })}>
            <AppLogo size={32} />
            <span className={s.navTitle}>Alertas Judiciales</span>
          </div>
          <div className={s.navLinks}>
            <a href="#features" className={s.navLink}>Features</a>
            <a href="#pricing" className={s.navLink}>Precios</a>
            <a href="#faq" className={s.navLink}>FAQ</a>
            <button className="theme-toggle" onClick={toggleTheme}>
              {theme === "dark" ? "\u2600\uFE0F" : "\uD83C\uDF19"}
            </button>
            <button className={s.navCta} onClick={goLogin}>
              Iniciar sesion
            </button>
          </div>
        </div>
      </nav>

      {/* ── Hero ── */}
      <section className={s.hero}>
        <div className={s.heroGlow1} />
        <div className={s.heroGlow2} />
        <div className={s.heroDots} />

        <div className={s.heroContent}>
          <div className={s.badge}>
            <span className={s.badgeDot} />
            Monitoreo judicial automatizado
          </div>

          <h1 className={s.heroTitle}>
            Nunca pierdas<br />
            una actuacion judicial
          </h1>

          <p className={s.heroSubtitle}>
            Monitoreo automatico de procesos en SAMAI y Rama Judicial.
            Alertas diarias por email. Dashboard en tiempo real.
            <strong> Gratis para siempre.</strong>
          </p>

          <div className={s.ctaGroup}>
            <button className={s.ctaPrimary} onClick={goSignup}>
              Comenzar gratis
            </button>
            <a href="#features" className={s.ctaSecondary}>
              Ver como funciona
            </a>
          </div>

          <p className={s.heroCaption}>
            Sin tarjeta de credito &middot; 5 procesos gratis &middot; Configuracion en 2 minutos
          </p>
        </div>

        {/* Hero visual — dashboard mockup */}
        <RevealSection className={s.heroVisual}>
          <div className={s.mockupWindow}>
            <div className={s.mockupBar}>
              <span /><span /><span />
            </div>
            <div className={s.mockupContent}>
              <div className={s.mockupSidebar}>
                <div className={s.mockupSidebarItem} />
                <div className={s.mockupSidebarItem} />
                <div className={s.mockupSidebarItem} />
              </div>
              <div className={s.mockupMain}>
                <div className={s.mockupStatRow}>
                  <div className={s.mockupStat}><span>12</span>Procesos</div>
                  <div className={s.mockupStat}><span>8</span>Activos</div>
                  <div className={s.mockupStat}><span>3</span>Alertas hoy</div>
                </div>
                <div className={s.mockupCards}>
                  <div className={s.mockupCard}>
                    <div className={s.mockupCardTitle}>Rad. 11001-03-26-000-2024-00156</div>
                    <div className={s.mockupCardBadge}>Nueva actuacion</div>
                  </div>
                  <div className={s.mockupCard}>
                    <div className={s.mockupCardTitle}>Rad. 25000-23-36-000-2023-00892</div>
                    <div className={s.mockupCardMuted}>Sin novedades</div>
                  </div>
                  <div className={s.mockupCard}>
                    <div className={s.mockupCardTitle}>Rad. 76001-23-33-000-2024-00234</div>
                    <div className={s.mockupCardBadge}>Sentencia</div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </RevealSection>
      </section>

      {/* ── Social proof bar ── */}
      <RevealSection className={s.proofBar}>
        <div className={s.proofInner}>
          <div className={s.proofItem}>
            <strong>342</strong>
            <span>Juzgados administrativos cubiertos</span>
          </div>
          <div className={s.proofDivider} />
          <div className={s.proofItem}>
            <strong>2+</strong>
            <span>Fuentes judiciales cubiertas</span>
          </div>
          <div className={s.proofDivider} />
          <div className={s.proofItem}>
            <strong>7 AM</strong>
            <span>Alertas antes de iniciar tu dia</span>
          </div>
        </div>
      </RevealSection>

      {/* ── Pain section ── */}
      <section className={s.painSection}>
        <RevealSection>
          <h2 className={s.sectionTitle}>El problema que resolvemos</h2>
          <p className={s.sectionSubtitle}>
            Si litigas en lo contencioso-administrativo, esto te suena familiar:
          </p>
        </RevealSection>
        <div className={s.painGrid}>
          <RevealSection className={s.painCard} delay={0}>
            <span className={s.painIcon}>{"\u23F0"}</span>
            <h3>Horas revisando portales</h3>
            <p>Entrar a SAMAI, Rama Judicial, buscar cada radicado, comparar actuaciones... todos los dias. Tiempo que podrias usar litigando.</p>
          </RevealSection>
          <RevealSection className={s.painCard} delay={100}>
            <span className={s.painIcon}>{"\u26A0\uFE0F"}</span>
            <h3>Actuaciones que se pasan</h3>
            <p>Un auto admisorio, una fijacion en lista, un traslado. Si no lo ves a tiempo, pierdes terminos.</p>
          </RevealSection>
          <RevealSection className={s.painCard} delay={200}>
            <span className={s.painIcon}>{"\uD83D\uDCB8"}</span>
            <h3>Herramientas caras</h3>
            <p>La competencia cobra $1.000+ por proceso por mes. Con 50 procesos, son $50.000/mes solo en monitoreo.</p>
          </RevealSection>
        </div>
      </section>

      {/* ── Features bento ── */}
      <section id="features" className={s.featuresSection}>
        <RevealSection>
          <h2 className={s.sectionTitle}>Todo lo que necesitas</h2>
          <p className={s.sectionSubtitle}>
            Disenado por y para abogados administrativistas colombianos.
          </p>
        </RevealSection>
        <div className={s.bentoGrid}>
          {FEATURES.map((f, i) => (
            <RevealSection
              key={f.title}
              className={`${s.bentoCard} ${f.span === "wide" ? s.bentoWide : ""}`}
              delay={i * 80}
            >
              <span className={s.bentoIcon}>{f.icon}</span>
              <h3>{f.title}</h3>
              <p>{f.desc}</p>
            </RevealSection>
          ))}
        </div>
      </section>

      {/* ── Pricing ── */}
      <section id="pricing" className={s.pricingSection}>
        <RevealSection>
          <h2 className={s.sectionTitle}>Precios simples y transparentes</h2>
          <p className={s.sectionSubtitle}>
            Sin sorpresas. Sin "contactenos para cotizacion". Empieza gratis hoy.
          </p>
        </RevealSection>
        <div className={s.pricingGrid}>
          {PLANS.map((plan, i) => (
            <RevealSection
              key={plan.name}
              className={`${s.pricingCard} ${plan.highlighted ? s.pricingHighlighted : ""}`}
              delay={i * 100}
            >
              {plan.highlighted && <div className={s.pricingBadge}>Mas popular</div>}
              <h3 className={s.pricingName}>{plan.name}</h3>
              <div className={s.pricingPrice}>
                <span>{plan.price}</span>
                <small>{plan.period}</small>
              </div>
              <p className={s.pricingProcesses}>{plan.processes}</p>
              <ul className={s.pricingFeatures}>
                {plan.features.map((f) => (
                  <li key={f}>{"\u2713"} {f}</li>
                ))}
              </ul>
              <button
                className={plan.highlighted ? s.ctaPrimary : s.ctaOutline}
                onClick={goSignup}
              >
                {plan.cta}
              </button>
            </RevealSection>
          ))}
        </div>
      </section>

      {/* ── FAQ ── */}
      <section id="faq" className={s.faqSection}>
        <RevealSection>
          <h2 className={s.sectionTitle}>Preguntas frecuentes</h2>
        </RevealSection>
        <div className={s.faqList}>
          {FAQS.map((f) => (
            <FaqItem key={f.q} q={f.q} a={f.a} />
          ))}
        </div>
      </section>

      {/* ── Final CTA ── */}
      <section className={s.finalCta}>
        <div className={s.heroGlow1} />
        <div className={s.heroGlow2} />
        <RevealSection className={s.finalCtaInner}>
          <h2>Empieza a monitorear tus procesos hoy</h2>
          <p>5 procesos gratis. Sin tarjeta. Configuracion en 2 minutos.</p>
          <button className={s.ctaPrimary} onClick={goSignup}>
            Crear cuenta gratis
          </button>
        </RevealSection>
      </section>

      {/* ── Footer ── */}
      <footer className={s.footer}>
        <div className={s.footerInner}>
          <div className={s.footerBrand}>
            <AppLogo size={24} />
            <span>Alertas Judiciales by Dertyos</span>
          </div>
          <div className={s.footerLinks}>
            <a href="/privacidad">Privacidad</a>
            <a href="/terminos">Terminos</a>
            <a href="mailto:soporte@dertyos.com">Contacto</a>
          </div>
          <p className={s.footerCopy}>
            &copy; {new Date().getFullYear()} Dertyos. Todos los derechos reservados.
          </p>
        </div>
      </footer>
    </div>
  );
}
