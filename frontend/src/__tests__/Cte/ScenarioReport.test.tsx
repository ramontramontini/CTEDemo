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

const mockResults: Record<string, ScenarioResult> = {
  'happy-path': { statusCode: 201, body: { id: '1', status: 'GERADO' }, passed: true },
  'carrier-not-found': { statusCode: 400, body: { detail: 'Carrier not found' }, passed: false },
};

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

describe('ScenarioReport', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('AC1: Report Button Visibility', () => {
    it('does not show Ver Relatorio when no results exist', () => {
      renderPanel();
      expect(screen.queryByText('Ver Relatorio')).not.toBeInTheDocument();
    });

    it('shows Ver Relatorio button when results exist', () => {
      renderPanel({ results: mockResults });
      expect(screen.getByText('Ver Relatorio')).toBeInTheDocument();
    });
  });

  describe('AC2: Report Modal Content', () => {
    it('opens modal when Ver Relatorio is clicked', () => {
      renderPanel({ results: mockResults });
      fireEvent.click(screen.getByText('Ver Relatorio'));
      expect(screen.getByText('Relatorio de Cenarios')).toBeInTheDocument();
    });

    it('shows scenarios grouped by category in modal', () => {
      renderPanel({ results: mockResults });
      fireEvent.click(screen.getByText('Ver Relatorio'));
      // Category headers inside modal
      expect(screen.getByTestId('report-modal')).toBeInTheDocument();
      expect(screen.getByText('Relatorio de Cenarios')).toBeInTheDocument();
    });

    it('shows scenario names and status badges in modal', () => {
      renderPanel({ results: mockResults });
      fireEvent.click(screen.getByText('Ver Relatorio'));
      const modal = screen.getByTestId('report-modal');
      // Scenario names appear in modal cards
      expect(modal).toHaveTextContent('Cenario feliz');
      expect(modal).toHaveTextContent('Transportadora nao encontrada');
    });

    it('shows pass/fail indicators and actual status codes', () => {
      renderPanel({ results: mockResults });
      fireEvent.click(screen.getByText('Ver Relatorio'));
      const modal = screen.getByTestId('report-modal');
      expect(modal).toHaveTextContent('201');
      expect(modal).toHaveTextContent('400');
      // Pass icon for happy-path, fail icon for carrier-not-found
      expect(modal).toHaveTextContent('\u2713');
      expect(modal).toHaveTextContent('\u2717');
    });

    it('shows JSON response body expanded (not collapsed)', () => {
      renderPanel({ results: mockResults });
      fireEvent.click(screen.getByText('Ver Relatorio'));
      const modal = screen.getByTestId('report-modal');
      expect(modal).toHaveTextContent('"status": "GERADO"');
      expect(modal).toHaveTextContent('"detail": "Carrier not found"');
    });

    it('shows summary line in modal header', () => {
      renderPanel({ results: mockResults });
      fireEvent.click(screen.getByText('Ver Relatorio'));
      const modal = screen.getByTestId('report-modal');
      expect(modal).toHaveTextContent('1/2 passaram');
    });
  });

  describe('AC3: Copy JSON Per Card', () => {
    it('shows Copiar JSON button for each card with results', () => {
      renderPanel({ results: mockResults });
      fireEvent.click(screen.getByText('Ver Relatorio'));
      expect(screen.getAllByText('Copiar JSON')).toHaveLength(2);
    });

    it('copies JSON to clipboard when Copiar JSON is clicked', async () => {
      const writeText = vi.fn().mockResolvedValue(undefined);
      Object.assign(navigator, { clipboard: { writeText } });

      renderPanel({ results: mockResults });
      fireEvent.click(screen.getByText('Ver Relatorio'));
      const copyButtons = screen.getAllByText('Copiar JSON');
      fireEvent.click(copyButtons[0]);

      expect(writeText).toHaveBeenCalledWith(
        JSON.stringify(mockResults['happy-path'].body, null, 2),
      );
    });

    it('shows Copiado! feedback after successful copy', async () => {
      const writeText = vi.fn().mockResolvedValue(undefined);
      Object.assign(navigator, { clipboard: { writeText } });

      renderPanel({ results: mockResults });
      fireEvent.click(screen.getByText('Ver Relatorio'));
      const copyButtons = screen.getAllByText('Copiar JSON');
      fireEvent.click(copyButtons[0]);

      await waitFor(() => {
        expect(screen.getByText('Copiado!')).toBeInTheDocument();
      });
    });

    it('shows Erro ao copiar when clipboard fails', async () => {
      const writeText = vi.fn().mockRejectedValue(new Error('Not allowed'));
      Object.assign(navigator, { clipboard: { writeText } });

      renderPanel({ results: mockResults });
      fireEvent.click(screen.getByText('Ver Relatorio'));
      const copyButtons = screen.getAllByText('Copiar JSON');
      fireEvent.click(copyButtons[0]);

      await waitFor(() => {
        expect(screen.getByText('Erro ao copiar')).toBeInTheDocument();
      });
    });
  });

  describe('AC4: Modal Close', () => {
    it('closes modal when X button is clicked', () => {
      renderPanel({ results: mockResults });
      fireEvent.click(screen.getByText('Ver Relatorio'));
      expect(screen.getByTestId('report-modal')).toBeInTheDocument();

      fireEvent.click(screen.getByLabelText('Fechar'));
      expect(screen.queryByTestId('report-modal')).not.toBeInTheDocument();
    });

    it('closes modal when Escape key is pressed', () => {
      renderPanel({ results: mockResults });
      fireEvent.click(screen.getByText('Ver Relatorio'));
      expect(screen.getByTestId('report-modal')).toBeInTheDocument();

      fireEvent.keyDown(document, { key: 'Escape' });
      expect(screen.queryByTestId('report-modal')).not.toBeInTheDocument();
    });

    it('closes modal when backdrop is clicked', () => {
      renderPanel({ results: mockResults });
      fireEvent.click(screen.getByText('Ver Relatorio'));
      const backdrop = screen.getByTestId('report-modal');

      fireEvent.click(backdrop);
      expect(screen.queryByTestId('report-modal')).not.toBeInTheDocument();
    });

    it('does not close modal when content inside is clicked', () => {
      renderPanel({ results: mockResults });
      fireEvent.click(screen.getByText('Ver Relatorio'));
      expect(screen.getByTestId('report-modal')).toBeInTheDocument();

      fireEvent.click(screen.getByText('Relatorio de Cenarios'));
      expect(screen.getByTestId('report-modal')).toBeInTheDocument();
    });
  });
});
