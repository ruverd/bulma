# Tickets

Tracker: DEV-5001
Spec: SPEC.md

## Ticket 1: Primary button uses brand-600

- **Status:** pending
- **Blocked by:** none
- **Seam:** Button variant map
- **RED:** `Button.test.tsx` asserts `bg-brand-600` on `variant="primary"`
- **GREEN:** swap the class in the variant map
- **Acceptance:**
  - primary button background is brand-600
  - other variants unchanged
- **Files:** `src/shared/ui/Button.tsx`, `src/shared/ui/Button.test.tsx`

## Ticket 2: Tenant switcher keeps the session

- **Status:** pending
- **Blocked by:** Ticket 1
- **Seam:** session store
- **RED:** switching tenant keeps the user signed in
- **GREEN:** reuse the refresh token across tenants
- **Acceptance:**
  - switching tenant does not log out
- **Files:** `src/auth/session.ts`, `src/tenants/switcher.tsx`

## Ticket 3: Inbox empty state copy

- **Status:** pending
- **Blocked by:** none
- **Seam:** Inbox view
- **RED:** empty inbox shows "Nothing here yet"
- **GREEN:** new copy string
- **Acceptance:**
  - copy matches the ticket
- **Files:**
