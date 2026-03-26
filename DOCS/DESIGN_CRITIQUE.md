# Design Critique — Alertas Judiciales
## Fecha: 26 de marzo de 2026
## Herramienta: Claude Code `/design-critique`

---

## Overall Impression

La arquitectura CSS y la funcionalidad están bien construidas: tokens centralizados, dark mode funcional, responsive base, skeleton loading. El gap está en **accesibilidad** (varios criterios WCAG fallando), **identidad de marca** (parece prototipo, no SaaS) y un par de patrones de interacción que no funcionan en móvil.

---

## Design Critique: Alertas Judiciales — Dashboard

### Usability

| Finding | Severity | Recommendation |
|---------|----------|----------------|
| Double-click para editar alias no funciona en móvil ni con teclado | 🔴 Critical | El menú `...` ya tiene "Editar alias" — es suficiente. Remover double-click o mantenerlo solo como atajo adicional |
| `alert()` nativo en DetalleRadicado (link copiar incógnito) | 🔴 Critical | Reemplazar con Toast — mismo sistema que ya existe en el proyecto |
| Inputs del Login sin `<label>` visible (solo placeholder) | 🔴 Critical | Agregar `<label>` semántico. Cuando el campo tiene contenido el usuario no sabe qué campo es |
| Página de detalle sin header/nav consistente | 🟡 Moderate | El usuario pierde el contexto de la app al entrar a `/radicado/:id`. Agregar header mínimo con nombre de app |
| "Actualizado 03:00 p.m." — formato de hora difícil de leer | 🟢 Minor | Usar formato más natural: "hace 5 min" o bien un tooltip con hora exacta |

### Visual Hierarchy

- **Primer elemento que capta la vista**: los números estadísticos (5, 5, 0) — correcto.
- **Flujo de lectura**: Stats → "Mis Radicados" → lista → "Alertas Recientes". Flujo lógico.
- **Problema**: Los radicados (`08573-40-89-003-2023-00242-00`) son el dato más importante para el abogado pero no tienen jerarquía suficiente. Están en monospace pero al mismo peso visual que el alias.
- **Botón "+ Agregar"**: bien posicionado, contraste adecuado.

### Consistency

| Element | Issue | Recommendation |
|---------|-------|----------------|
| Fuente tipográfica | `-apple-system, BlinkMacSystemFont...` — pila por defecto, sin personalidad | Usar Inter (Google Fonts, sin costo) |
| Logo/marca | "Alertas Judiciales / by Dertyos" en texto plano, sin logotipo | Agregar logo SVG mínimo o wordmark estilizado |
| `loading` state en botones | Usa `"..."` como indicador — no descriptivo | Texto descriptivo: `"Buscando..."`, `"Eliminando..."`, `"Cargando..."` |
| `<html lang="en">` | El idioma del documento es incorrecto | Cambiar a `lang="es"` — afecta lectores de pantalla |
| Emojis en empty states | `&#x2705;` (✅), `&#x1F4CB;` se ven diferente en cada SO | Reemplazar con SVG icons del mismo sistema de diseño |

### Accessibility

| Check | Result | Detail |
|-------|--------|--------|
| `--text-muted` (#9ca3af) sobre fondo blanco | 🔴 FALLA WCAG AA | Ratio ~2.8:1. Mínimo 4.5:1 para texto normal. Usar `#6b7280` o más oscuro |
| `--text-secondary` (#6b7280) sobre `--bg` (#f5f7fa) | 🟡 Marginal | Ratio ~4.2:1. Pasa AA para texto normal pero falla para texto pequeño (<18px bold) |
| Inputs Login sin `<label>` | 🔴 FALLA WCAG 1.3.1, 3.3.2 | Solo tienen `placeholder` — no accesible cuando hay contenido |
| Botón tema (🌙/☀️) sin `aria-label` descriptivo | 🔴 FALLA WCAG 4.1.2 | `title` no es leído por todos los screen readers. Agregar `aria-label="Cambiar a modo oscuro"` |
| Botón `...` (menú) sin `aria-label` | 🔴 FALLA WCAG 4.1.2 | Solo `title="Mas acciones"`. Agregar `aria-label` y `aria-expanded` |
| View toggle (grid/lista) sin `aria-label` | 🟡 Moderate | Los botones SVG no tienen texto accesible |
| `<html lang="en">` | 🔴 FALLA WCAG 3.1.1 | Idioma incorrecto afecta pronunciación en lectores de pantalla |
| Touch targets botones `...` y toggle | 🟡 Moderate | Área de click ~30x30px — mínimo recomendado 44x44px (WCAG 2.5.5) |
| Focus visible | 🟢 OK | Los inputs tienen focus ring con box-shadow. Botones heredan estilos del browser |

### What Works Well

- Design tokens en `theme.css` — excelente organización, fácil de cambiar identidad
- Dark mode con CSS variables — bien ejecutado, sin JS extra
- Skeleton loading — evita layout shift, profesional
- Sticky header con `backdrop-filter: blur` — moderno
- React Query con polling cada 60s — buen patrón para alertas en tiempo real
- Keyboard trap en modal (Escape para cerrar)
- Confirmación antes de eliminar (no usa `window.confirm`)
- Export CSV funcional en detalle
- Copy-to-clipboard del número de radicado

### Priority Recommendations

1. **[P0] Accesibilidad crítica** — Labels en inputs Login, aria-labels en botones icono, lang="es" en HTML, fix contraste text-muted
2. **[P0] Reemplazar alert() nativo** — usar Toast que ya existe
3. **[P1] Fuente web Inter** — diferencia inmediata en percepción de calidad
4. **[P1] Header consistente en DetalleRadicado** — contexto de navegación
5. **[P2] Logo/marca** — identidad visual del producto
6. **[P2] Historial de alertas leídas** — las alertas pasadas son valiosas para el abogado

---

## Detalle por Archivo

### `frontend/index.html`
- [ ] `lang="en"` → `lang="es"` (**WCAG 3.1.1**)
- [ ] Agregar `<link>` a Google Fonts Inter
- [ ] Agregar `<meta name="description">` para SEO básico

### `frontend/src/pages/Login.tsx`
- [ ] Inputs `email` y `password` no tienen `<label>` visible — solo placeholder
- [ ] Inputs de `resetPassword` (código, nueva contraseña) sin label

### `frontend/src/pages/Dashboard.tsx`
- [ ] Botón toggle tema: agregar `aria-label` dinámico
- [ ] Botones view toggle (grid/lista): agregar `aria-label` descriptivo
- [ ] Botón `aria-pressed` en view toggle para indicar estado activo

### `frontend/src/components/RadicadoCard.tsx`
- [ ] Botón `...`: agregar `aria-label="Más acciones"` y `aria-expanded={menuOpen}`
- [ ] Double-click como único mecanismo para iniciar edición en desktop — documentar que el menú también lo permite

### `frontend/src/pages/DetalleRadicado.tsx`
- [ ] `alert()` nativo en línea ~117 → reemplazar con Toast
- [ ] Página sin header de app — agregar barra de navegación mínima
- [ ] `actuacionSearch` input sin `<label>`

### `frontend/src/styles/theme.css`
- [ ] `--text-muted: #9ca3af` falla WCAG AA — cambiar a `#757985` (ratio 4.6:1)
- [ ] Agregar variable `--font-sans` apuntando a Inter

### `frontend/src/styles/forms.css`
- [ ] `label` tiene estilos pero Login.tsx no usa `<label>` — inconsistencia

---

## Plan de Implementación

### P0 — Accesibilidad crítica (implementar primero)
1. `index.html`: `lang="es"` + meta description + link Inter font
2. `theme.css`: fix `--text-muted` contraste + variable `--font-sans` Inter
3. `Login.tsx`: agregar `<label>` a todos los inputs
4. `Dashboard.tsx`: `aria-label` en botones icono + `aria-pressed` en view toggle
5. `RadicadoCard.tsx`: `aria-label` + `aria-expanded` en botón `...`
6. `DetalleRadicado.tsx`: reemplazar `alert()` con Toast + label en búsqueda + header

### P1 — Percepción de calidad
7. `theme.css` + `index.html`: Inter como fuente principal
8. `DetalleRadicado.tsx`: header consistente con nombre de app

### P2 — Valor y retención (backlog)
- Historial de alertas leídas
- Notificaciones push (PWA)
- Onboarding guiado para usuarios nuevos
- Logo/wordmark

---

*Generado por Claude Code — `/design-critique` skill*
