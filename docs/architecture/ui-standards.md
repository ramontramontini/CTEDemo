# UI Standards — CTEDemo

> Design system, Tailwind conventions, and component patterns for the CTEDemo frontend.

---

## Design Principles

1. **Clarity over decoration** — every element serves a purpose
2. **Consistency** — same patterns across all pages
3. **Information density** — developer tools show data, not chrome
4. **Responsive** — desktop-first (development cockpit), tablet-aware

---

## Color Palette

| Purpose | Tailwind Classes | Usage |
|---------|-----------------|-------|
| Primary | `bg-indigo-600`, `text-indigo-600` | Actions, links, active states |
| Success | `bg-green-600`, `text-green-600` | Done, passing, healthy |
| Warning | `bg-yellow-500`, `text-yellow-600` | In progress, attention needed |
| Danger | `bg-red-600`, `text-red-600` | Errors, blocked, failed |
| Neutral | `bg-gray-50` to `bg-gray-900` | Backgrounds, text, borders |

---

## Typography

| Element | Classes |
|---------|---------|
| Section heading | `text-xl font-semibold text-gray-800` |
| Card title | `text-lg font-medium text-gray-900` |
| Body text | `text-sm text-gray-600` |
| Label | `text-xs font-medium text-gray-500 uppercase tracking-wide` |

---

## Component Patterns

### Card
```html
<div class="rounded-lg border border-gray-200 bg-white p-4 shadow-sm">
  <h3 class="text-lg font-medium text-gray-900">Title</h3>
  <p class="mt-1 text-sm text-gray-600">Description</p>
</div>
```

### Status Badge
```html
<span class="inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium
  bg-green-100 text-green-800">  <!-- Done -->
  Done
</span>
```

| Status | Background | Text |
|--------|-----------|------|
| Todo | `bg-gray-100` | `text-gray-800` |
| Doing | `bg-yellow-100` | `text-yellow-800` |
| Done | `bg-green-100` | `text-green-800` |
| Blocked | `bg-red-100` | `text-red-800` |
| Canceled | `bg-gray-100` | `text-gray-500` |

### Button
```html
<!-- Primary -->
<button class="rounded-md bg-indigo-600 px-4 py-2 text-sm font-medium text-white
  hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-indigo-500">
  Action
</button>

<!-- Secondary -->
<button class="rounded-md border border-gray-300 bg-white px-4 py-2 text-sm font-medium
  text-gray-700 hover:bg-gray-50">
  Cancel
</button>
```

---

## Shared UI Primitives

> Reusable components in `frontend/src/components/shared/`. Source files are authoritative for current API — this section provides overview and usage guidance.

### Card

Consistent container with title, optional icon, and optional action slot. Accepts a `header` render slot for complex custom headers.

| Prop | Type | Required | Description |
|------|------|----------|-------------|
| `title` | `string` | No | Card heading (used when `header` is absent) |
| `icon` | `React.ReactNode` | No | Icon rendered beside title |
| `actions` | `React.ReactNode` | No | Action buttons in header |
| `header` | `React.ReactNode` | No | Custom header JSX — replaces the built-in title row when provided |
| `children` | `React.ReactNode` | Yes | Card body content |
| `className` | `string` | No | Additional CSS classes |
| `padding` | `string` | No | Tailwind padding class (default: `'p-6'`) |
| `ring` | `string` | No | Tailwind ring classes for border highlight (e.g. `'ring-2 ring-blue-200'`) |

```tsx
// Simple title usage (backward compatible)
<Card title="Story Details" icon={<BookOpen size={20} />}>
  <p>Content here</p>
</Card>

// Custom header slot
<Card header={<div className="flex items-center gap-2">...</div>} padding="p-5">
  <p>Content here</p>
</Card>
```

### ViewToggle

Generic toggle for switching between view modes (board/list, grid/table, etc.).

| Prop | Type | Required | Description |
|------|------|----------|-------------|
| `mode` | `T extends string` | Yes | Current active mode |
| `options` | `ViewOption<T>[]` | Yes | Available modes (`{value, icon, label?}`) |
| `onChange` | `(mode: T) => void` | Yes | Mode change callback |

```tsx
<ViewToggle
  mode={viewMode}
  options={[
    { value: 'board', icon: <LayoutGrid size={18} />, label: 'Board' },
    { value: 'list', icon: <List size={18} />, label: 'List' },
  ]}
  onChange={setViewMode}
/>
```

### FilterPills

Horizontal pill bar for multi-select filtering.

| Prop | Type | Required | Description |
|------|------|----------|-------------|
| `options` | `FilterOption[]` | Yes | Available filters (`{label, value}`) |
| `active` | `string[]` | Yes | Currently active filter values |
| `onToggle` | `(value: string) => void` | Yes | Toggle callback |
| `label` | `string` | No | Accessible group label |

```tsx
<FilterPills
  options={[{ label: 'Bug', value: 'bug' }, { label: 'Feature', value: 'feature' }]}
  active={activeFilters}
  onToggle={handleToggle}
/>
```

### SectionGroup

Collapsible section with title, optional count badge, and chevron toggle. The toggle button receives `aria-label="Collapse"` / `aria-label="Expand"` for accessibility.

| Prop | Type | Required | Description |
|------|------|----------|-------------|
| `title` | `string` | Yes | Section heading |
| `icon` | `React.ReactNode` | No | Icon rendered before title (e.g. a status dot) |
| `count` | `number` | No | Badge count displayed beside title |
| `defaultCollapsed` | `boolean` | No | Initial collapsed state (default: `false`) |
| `children` | `React.ReactNode` | Yes | Section content |
| `className` | `string` | No | Additional CSS classes |

```tsx
<SectionGroup title="In Progress" count={3}>
  {stories.map(s => <StoryCard key={s.id} story={s} />)}
</SectionGroup>

// With icon slot
<SectionGroup title="Expedite" icon={<span className="inline-block h-2.5 w-2.5 rounded-full bg-red-500" />}>
  {/* content */}
</SectionGroup>
```

### Chip Tokens

Shared Tailwind class constants for filter chips. Import from `frontend/src/components/shared/chipTokens.ts`.

| Export | Value | Use |
|--------|-------|-----|
| `CHIP_ACTIVE` | `'bg-white text-indigo-600 shadow-sm'` | Active/selected chip state |
| `CHIP_INACTIVE` | `'text-slate-500 hover:text-slate-700'` | Inactive chip state |
| `CHIP_LAYOUT` | `'rounded-xl px-4 py-2 text-xs font-black'` | Chip shape and typography |

```tsx
import { CHIP_ACTIVE, CHIP_INACTIVE, CHIP_LAYOUT } from '../shared/chipTokens';

<button className={`${CHIP_LAYOUT} ${isActive ? CHIP_ACTIVE : CHIP_INACTIVE}`}>
  {label}
</button>
```

---

## Layout

### PillToggle (Main Navigation)

Horizontal nav pills in the AppShell header. Allo-aligned styling.

| State | Classes |
|-------|---------|
| Layout | `rounded-full px-5 py-2 text-xs font-black uppercase tracking-widest transition-all` |
| Active | `bg-indigo-600 text-white shadow-lg shadow-indigo-100` |
| Inactive | `bg-white text-slate-400 border border-slate-200 hover:text-slate-600` |

Page headings are removed — PillToggle is the sole page indicator.

### Page Layout
```
+----------------------------------------------------------+
|  Header (fixed, h-16, PillToggle = page indicator)        |
+--------+-------------------------------------------------+
|         |  Main Content                                    |
|         |  +-------------------------------------------+  |
|         |  | Content Area (scrollable)                  |  |
|         |  |                                            |  |
|         |  +-------------------------------------------+  |
+---------+-------------------------------------------------+
```

### Kanban Board Layout
```
+----------+----------+----------+----------+
| Todo     | Doing    | Done     | Archive  |
+----------+----------+----------+----------+
| [Card]   | [Card]   | [Card]   |          |
| [Card]   | [Card]   |          |          |
| [Card]   |          |          |          |
+----------+----------+----------+----------+
```

---

## Spacing

| Context | Value |
|---------|-------|
| Page padding | `p-6` |
| Card padding | `p-4` |
| Between sections | `space-y-6` |
| Between cards | `space-y-3` or `gap-4` |
| Between elements in card | `space-y-2` |

---

## Icons

Use [lucide-react](https://lucide.dev/) icons. Size conventions: `size={18}` for inline/toolbar icons, `size={20}` for card headers, `size={24}` for standalone/page-level icons. Import individually: `import { BookOpen } from 'lucide-react'`.

---

*DRAFT — design system will be refined as UI stories are implemented.*
