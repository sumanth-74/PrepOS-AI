# Mobile UX Checklist (P11.11)

## Portals audited
- [x] Student Portal — responsive nav, collapsible sidebar, timeline page
- [x] Mentor Portal — faculty workspace uses shared AppShell mobile menu
- [x] Admin Portal — dashboard pages use `p-4 sm:p-6` and flex-wrap actions

## Layout
- [x] AppShell hamburger menu on viewports below `lg`
- [x] Copilot panel scrollable on small screens
- [x] Admin metric grids collapse to 1–2 columns on mobile

## Touch targets
- [x] Buttons use minimum padding via `btn-secondary` / `btn-primary` classes
- [x] Copilot expand/collapse cards use full-width tap areas

## Devices
- [x] Android — Chrome responsive layout verified via Tailwind breakpoints
- [x] iPhone — safe-area friendly padding on page containers
- [x] Tablet — `md:` and `lg:` grids for faculty and admin dashboards

## Copilot
- [x] Rich cards replace long text blocks where structured data exists
- [x] Expand/collapse for card details
- [x] Explain sections for forecasts and recommendations

## Follow-ups
- [ ] Playwright mobile viewport E2E for `/student/timeline` and `/faculty`
- [ ] PWA install prompt (future)
