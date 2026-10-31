# Orbit interface system

Orbit is a calm local workspace for project work. The interface puts the current
mission ahead of configuration and keeps actions close to their evidence.
This system is implemented in the desktop source; no external UI dependency or
remote font/image download is required.

## Theme and foundations

`apps/desktop/src/theme.css` owns the theme contract: semantic colors, surface
levels, type families/sizes, spacing steps, radii and shadows. The default Forest
night theme uses ink-green surfaces, warm off-white text and a pale sage accent.
The light theme uses chalk surfaces, deep green text and a darker green accent.
The sidebar theme control switches themes for the current session. Never use a
provider's identity as the application's theme or assign fixed roles by provider.

Use semantic tokens rather than one-off colors. Reserve the accent for the
primary action, active navigation, focus and positive readiness. Amber means
attention/review; neutral means unknown or inactive. Status always has a text
label, so color is never the only signal. Unknown capacity is not a percentage.
Typography uses installed system fonts; run evidence uses the system monospace.
The spacing scale is 4/8/12/16/20/24/32/40/48 px. Cards use 12 px radii, controls 7 px.

## Component library

`apps/desktop/src/design-system.tsx` provides the shared React primitives:

- `Button`: primary, secondary, quiet and danger variants with common focus,
  disabled, hover and size behavior. Use one primary action per decision context.
- `Icon`: consistent inline SVG icons; decorative and hidden from assistive tech.
- `Panel`: shared bordered surface with optional layout classes.
- `Badge`: status text/dot with semantic attention, active, success and neutral tones.
- `PageHeading`: eyebrow, page title, concise purpose and optional page action.
- `EmptyState`: meaningful title, short explanation and optional next action.
- `Tabs`: linked tabs/panels, selected state, roving tab stop and arrow/Home/End keys.

Native labeled inputs, selects, checkboxes, disclosures and fieldsets share the
theme. Keep native form semantics; do not replace controls with clickable divs.

## Workspace patterns

A persistent navigation rail contains Missions, Agents, Models & capacity and
Workspace setup. The project switcher stays in the top bar. Only the selected
product view is exposed; setup forms do not compete with ongoing work.
The disconnected welcome state explains the next step without fabricated agents,
projects, capacity or activity.

Missions use a focused list/detail layout. Select one mission to act on it.
The New mission composer opens on demand, retains a closed draft, and closes on
successful creation. Overview, Changes & logs and Activity show evidence in
separate panes. Detailed execution metadata sits behind a disclosure; the diff
remains plain escaped text. File-access settings appear for assigned tasks;
reviewer selection appears for ready/review states as appropriate. Cancellation
uses the danger treatment. Changing mission clears pending file approval.

At smaller widths the rail becomes labeled-for-assistive-tech icons and the
mission panes become a single column. Reduced-motion preferences are respected.
Keep visible focus indicators and explicit labels. Do not silently grant file
access, approve review, merge a branch, or turn placeholder capacity into telemetry.

## Validation and limits

Interaction checks cover navigation, session theme switching, composer draft
retention, focused mission selection and keyboard detail tabs, alongside existing
agent/project/task/run flows. Browser visual checks use disconnected real product
states and disposable saved local-smoke data, never invented user configuration.
Native packaging remains a separate validation gate. This is a compact source
component library, not a claim of a fully audited accessibility certification.
