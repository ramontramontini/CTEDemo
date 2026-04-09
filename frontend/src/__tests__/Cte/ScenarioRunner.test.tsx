import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ScenarioPanel } from '@/pages/Cte/components/ScenarioPanel';
import type { Scenario } from '@/pages/Cte/scenarios';
import type { ScenarioResult } from '@/pages/Cte/hooks/useScenarioRunner';

const mockScenarios: Scenario[] = [
  {
    id: 'happy-path',
    name: 'Cenario feliz',
    description: 'Payload valido',
    category: 'success',
    expectedStatus: 201,
    expectedOutcome: '201 — CT-e gerado',
    payload: { FreightOrder: '001' },
  },
  {
    id: 'carrier-not-found',
    name: 'Transportadora nao encontrada',
    description: 'CNPJ nao cadastrado',
    category: 'business_error',
    expectedStatus: 400,
    expectedOutcome: '400 — Not found',
    payload: { FreightOrder: '002' },
  },
];

function renderPanel(overrides: {
  results?: Record<string, ScenarioResult>;
  runningId?: string | null;
  isRunningAll?: boolean;
} = {}) {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  const props = {
    scenarios: mockScenarios,
    onSelect: vi.fn(),
    selectedId: null,
    onRunOne: vi.fn(),
    onRunAll: vi.fn(),
    results: overrides.results ?? {},
    runningId: overrides.runningId ?? null,
    isRunningAll: overrides.isRunningAll ?? false,
  };
  render(
    <QueryClientProvider client={queryClient}>
      <ScenarioPanel {...props} />
    </QueryClientProvider>,
  );
  return props;
}

describe('ScenarioRunner', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders Executar Todos button', () => {
    renderPanel();
    expect(screen.getByText('Executar Todos')).toBeInTheDocument();
  });

  it('renders Executar button per card', () => {
    renderPanel();
    expect(screen.getAllByText('Executar')).toHaveLength(2);
  });

  it('calls onRunAll when Executar Todos clicked', () => {
    const props = renderPanel();
    fireEvent.click(screen.getByText('Executar Todos'));
    expect(props.onRunAll).toHaveBeenCalledTimes(1);
  });

  it('calls onRunOne with scenario id when individual Executar clicked', () => {
    const props = renderPanel();
    fireEvent.click(screen.getAllByText('Executar')[0]);
    expect(props.onRunOne).toHaveBeenCalledWith('happy-path');
  });

  it('shows pass indicator when status matches expected', () => {
    renderPanel({
      results: {
        'happy-path': { statusCode: 201, body: { id: '1' }, passed: true },
      },
    });
    const passIcon = screen.getByTestId('result-happy-path');
    expect(passIcon.textContent).toContain('201');
  });

  it('shows fail indicator when status does not match', () => {
    renderPanel({
      results: {
        'happy-path': { statusCode: 500, body: { detail: 'error' }, passed: false },
      },
    });
    const failIcon = screen.getByTestId('result-happy-path');
    expect(failIcon.textContent).toContain('500');
  });

  it('shows summary line when results exist', () => {
    renderPanel({
      results: {
        'happy-path': { statusCode: 201, body: {}, passed: true },
        'carrier-not-found': { statusCode: 400, body: {}, passed: true },
      },
    });
    expect(screen.getByText('2/2 passaram')).toBeInTheDocument();
  });

  it('shows spinner on running card', () => {
    renderPanel({ runningId: 'happy-path' });
    expect(screen.getByTestId('spinner-happy-path')).toBeInTheDocument();
  });
});
