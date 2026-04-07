# Frontend Architecture Guide — CTEDemo

> React 19 + TypeScript + Tailwind CSS patterns and conventions.

---

## Directory Structure

```
frontend/src/
├── api/                   # Data layer
│   ├── apiService.ts      # Axios HTTP client — all REST endpoints
│   └── hooks/             # React Query hooks (one file per aggregate)
│       ├── queryKeys.ts   # Shared cache key constants
│       ├── useBoard.ts    # Board aggregate query
│       ├── useStories.ts  # Story queries + mutations
│       ├── useEpics.ts    # Epic queries + mutations
│       ├── useAgents.ts   # Agent queries + mutations
│       ├── useQueue.ts    # Queue queries + mutations
│       ├── useWebSocket.ts# Real-time event hook
│       └── index.ts       # Barrel export
├── types/                 # TypeScript interfaces mirroring backend DTOs
│   └── index.ts           # All enums, interfaces, request/response types
├── components/            # Reusable UI components
│   ├── common/            # Shared: Button, Modal, Card, etc.
│   ├── layout/            # Layout: Header, Sidebar, PageContainer
│   └── {aggregate}/       # Aggregate-specific: StoryCard, EpicBoard
├── pages/                 # Route-level page components
├── __tests__/             # Component tests (Vitest + RTL)
└── test/                  # Test setup and utilities
```

---

## Component Patterns

### Functional Components Only
```tsx
interface StoryCardProps {
  story: Story;
  onTransition: (storyId: string, target: StoryStatus) => void;
}

function StoryCard({ story, onTransition }: StoryCardProps) {
  return (
    <div className="rounded-lg border p-4 shadow-sm">
      <h3 className="text-lg font-semibold">{story.title}</h3>
      <StatusBadge status={story.status} />
    </div>
  );
}
```

### Rules
- Max 200 lines per component
- Max 50 lines per function
- Props via TypeScript interfaces — no `any`
- No business logic — rendering only
- Data from API hooks, never computed locally

---

## Data Layer

### TypeScript Types (`types/index.ts`)
All frontend types mirror backend DTOs exactly. Enums use `as const` object pattern for both value and type:
```tsx
export const StoryStatus = {
  SPECIFYING: 'specifying',
  READY_TO_PULL: 'ready_to_pull',
  // ...
} as const;
export type StoryStatus = (typeof StoryStatus)[keyof typeof StoryStatus];
```

### API Service (`api/apiService.ts`)
Single Axios instance with all REST methods. Exported as `apiService` object:
```tsx
const client = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000',
});

export const apiService = {
  getStories,    // GET /api/v1/stories (paginated)
  getStory,      // GET /api/v1/stories/:id
  createStory,   // POST /api/v1/stories
  // ... all endpoints grouped by aggregate
};
```

### React Query Hooks (`api/hooks/`)
One hook file per aggregate. Each provides `useQuery` for reads and `useMutation` for writes with automatic cache invalidation:
```tsx
// Read hook — returns { data, isLoading, error }
export function useBoard() {
  return useQuery({
    queryKey: QUERY_KEYS.board,
    queryFn: () => apiService.getBoard(),
    staleTime: 5_000,
  });
}

// Mutation hook — invalidates related caches on success
export function useCreateStory() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (body: CreateStoryRequest) => apiService.createStory(body),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.stories });
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.board });
    },
  });
}
```

### Cache Key Strategy (`api/hooks/queryKeys.ts`)
Centralized query keys prevent cache key drift:
```tsx
export const QUERY_KEYS = {
  board: ['board'],
  stories: ['stories'],
  epics: ['epics'],
  agents: ['agents'],
  queue: ['queue'],
} as const;
```

**Stale times by aggregate:**
| Hook | Stale Time | Rationale |
|------|-----------|-----------|
| `useBoard` | 5s | Board is the primary view, needs freshness |
| `useStories` / `useEpics` / `useAgents` | 30s | List views update less frequently |
| `useQueueAvailable` | 10s | Queue changes with agent activity |

---

## WebSocket Integration

`useWebSocket()` provides real-time updates by connecting to `ws://{host}/api/v1/ws/events`.

**Key behaviors:**
- Auto-reconnect with exponential backoff (1s, 2s, 4s, max 30s)
- Parses JSON events and dispatches by `type` field
- Invalidates React Query caches per event type:
  - `story_transition` → board, stories, epics
  - `agent_status` → board, agents
  - `queue_update` → board, queue
  - `agent_output` → forwarded via `onEvent` callback only (no cache invalidation)
- Ping/pong keep-alive every 30s
- Cleanup on unmount (close connection, clear timers)

```tsx
const { isConnected } = useWebSocket({
  onEvent: (event) => {
    // Custom handling for specific event types
  },
});
```

---

## State Management

- **Server state:** React Query (TanStack Query) — caching, background refetch, optimistic updates
- **Real-time state:** WebSocket hook invalidates React Query caches on server events
- **UI state:** `useState` / `useReducer` for local component state
- **Shared state:** React Context for cross-component state (theme, user, filters, panel visibility)
  - `ProjectContext` — selected project ID
  - `ChatPanelContext` — chat panel open/close state (persists across route navigation)

---

## Error Handling

### Architecture Overview

Frontend error handling uses a four-layer architecture:

```
Mutation / API call fails
  ↓
MutationCache.onError (module scope — outside React tree)
  ↓
ErrorBridge.emit(error) — pub/sub crosses React boundary
  ↓
ErrorContext.showApiError() — React context, subscribed via useEffect
  ↓
ErrorDialog renders — user-friendly title, message, technical details
```

### ErrorBridge (Module-Scope Pub/Sub)

Connects `QueryClient.MutationCache` (created at module scope, outside React tree) to `ErrorProvider` (inside React tree):

```typescript
type ErrorSubscriber = (error: unknown) => void;
const subscribers = new Set<ErrorSubscriber>();

export const errorBridge = {
  subscribe(fn: ErrorSubscriber): () => void { /* add + return unsubscribe */ },
  emit(error: unknown): void { /* notify all subscribers */ },
  clear(): void { /* test-only: remove all subscribers */ },
};
```

**Why:** React Query's `MutationCache` is created outside React. React Context is inside React. The bridge connects them with a lightweight pub/sub.

### ErrorContext (React Context)

```typescript
interface ErrorContextType {
  showError: (title: string, message: string, details?: ErrorDetails) => void;
  showApiError: (error: unknown, customMessage?: string) => void;
  clearError: () => void;
}
```

**Key behaviors:**
- Subscribes to `errorBridge` in `useEffect` — receives all mutation errors
- Extracts backend message from FastAPI format (`{detail: "..."}`) or custom format (`{error: "...", detail: null}`)
- Maps HTTP status to user-friendly title:

| Status | Title |
|--------|-------|
| 400 | Invalid Request |
| 401 | Authentication Required |
| 403 | Access Denied |
| 404 | Not Found |
| 409 | Conflict |
| 422 | Validation Error |
| 500+ | Server Error |

### ErrorDialog (User-Facing UI)

- Displays user-friendly title and message
- Collapsible "Technical Details" section with: timestamp, endpoint, HTTP status, error ID, error message, stack trace
- "Copy Error Details" button formats all details into structured text for support
- Red alert icon, white dialog on dark backdrop

### ErrorBoundary (Render Errors)

React Error Boundary class component for unhandled render errors:
- Catches errors via `getDerivedStateFromError()`
- Displays fallback UI with error message and "Reload Application" button
- Logs to console via `componentDidCatch()`

### ApiError Interface

Typed error transformation in the API service layer:

```typescript
export interface ApiError {
  code: string;      // e.g., "NOT_FOUND", "VALIDATION_ERROR"
  message: string;   // User-friendly message
  details?: unknown; // Structured details from backend
  status: number;    // HTTP status code
}
```

**`transformError()` handles:**
- AxiosError with response → extracts status, message from `data.detail` or `data.message`
- Network errors (ECONNABORTED, timeout) → `TIMEOUT` code
- Connection failures → `NETWORK_ERROR` code
- Unknown errors → `UNKNOWN` code with HTTP 500

**Status → code mapping:**
`400→BAD_REQUEST` | `401→UNAUTHORIZED` | `403→FORBIDDEN` | `404→NOT_FOUND` | `409→CONFLICT` | `422→VALIDATION_ERROR` | `429→RATE_LIMITED` | `500→SERVER_ERROR`

---

## Styling with Tailwind

- Use utility classes directly — no custom CSS unless absolutely necessary
- Follow design system in `docs/architecture/ui-standards.md`
- Common patterns extracted to component abstractions, not CSS classes
