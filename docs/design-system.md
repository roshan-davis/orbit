# Orbit interface system

Orbit is a calm local workspace for project work. The interface puts the current
mission ahead of configuration and keeps actions close to their evidence.
This system is implemented in the desktop source; no external UI dependency or
remote font/image download is required.

## Theme and foundations

`apps/desktop/src/theme.css` owns the theme contract: semantic colors, surface
levels, type families/sizes, spacing steps, radii and shadows. The default Dusk
night theme uses neutral slate surfaces, soft white text and a lavender accent.
The Alabaster light theme uses cool white surfaces, deep neutral text and indigo actions.
The approved eight-page Antigravity / Google Stitch reference supplies visual direction;
ORB-008 records provenance and corrections to unsupported reference claims.
The sidebar theme control switches themes for the current session. Never use a
provider's identity as the application's theme or assign fixed roles by provider.

Use semantic tokens rather than one-off colors. Reserve the accent for the
primary action, active navigation, focus and selected state. Mint indicates a recorded successful outcome, never inferred readiness. Amber means
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

## Focused mission decisions (ORB-008)

A compact summary replaces dashboard cards. The selected mission explains its next
step using recorded state. Dependencies, assignment history and optional agent
configuration use native disclosures. File grants open at the assigned step; grants
reset on mission, assignment and scope changes. Context is limited to 65,536 UTF-8
bytes across at most 16 files, not characters; no speculative usage meter is shown.

Review excludes prior authors from the configured identity picker. The human session
records a completed review assertion; Orbit does not run an independent reviewer.
Request revision returns through ready and a new assignment. Final completion needs
a separate note and explicit checkbox and never merges or pushes Git.

No Emergency Stop, persona testing, identity forking, DAG editor, automatic testing
or telemetry is implied. Model inventory alone is not execution readiness.

## Help guide

`apps/desktop/src/help.tsx` owns current workflow guidance and examples; `help.css`
uses the existing semantic tokens. Help remains available offline and while other
requests are pending. Search filters complete topics, including disclosed detail
text. The guide leads with bundled SVG diagrams, with independently composed vertical
versions for narrow windows. Every image has meaningful alternative text and a
visible text equivalent. Native topic links and disclosures support keyboard use.
Update affected guidance in the same PR as user-facing behavior (see AGENTS.md).

Help has a separate Learn landmark in the sidebar. Real tutorial screenshots
include numbered pointers, explicit example-data captions and a keyboard-operable
native dialog for enlargement. Preserve Escape close and return focus. Refresh
affected diagrams/screenshots alongside guidance when workflows change.
