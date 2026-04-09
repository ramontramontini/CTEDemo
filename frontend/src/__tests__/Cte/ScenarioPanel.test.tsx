import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { ScenarioPanel } from '@/pages/Cte/components/ScenarioPanel';
import type { Scenario } from '@/pages/Cte/scenarios';

const mockScenarios: Scenario[] = [
  {
    id: 'happy-path',
    name: 'Cenario feliz',
    description: 'Payload valido completo',
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
  {
    id: 'invalid-cnpj',
    name: 'CNPJ invalido',
    description: 'Digito verificador incorreto',
    category: 'validation_error',
    expectedStatus: 422,
    expectedOutcome: '422 — CNPJ invalido',
    payload: { FreightOrder: '003' },
  },
  {
    id: 'cfop-cross-state',
    name: 'CFOP 5xxx interestadual',
    description: 'CFOP requer mesmo estado',
    category: 'cfop_error',
    expectedStatus: 422,
    expectedOutcome: '422 — CFOP requer mesmo estado',
    payload: { FreightOrder: '004' },
  },
];

describe('ScenarioPanel', () => {
  it('renders all category headers', () => {
    render(
      <ScenarioPanel scenarios={mockScenarios} onSelect={vi.fn()} selectedId={null} />
    );
    expect(screen.getByText(/Sucesso/)).toBeInTheDocument();
    expect(screen.getByText(/Erro de Negocio/)).toBeInTheDocument();
    expect(screen.getByText(/Erro de Validacao/)).toBeInTheDocument();
    expect(screen.getByText(/Erro CFOP/)).toBeInTheDocument();
  });

  it('renders scenario cards with name and description', () => {
    render(
      <ScenarioPanel scenarios={mockScenarios} onSelect={vi.fn()} selectedId={null} />
    );
    expect(screen.getByText('Cenario feliz')).toBeInTheDocument();
    expect(screen.getByText('Payload valido completo')).toBeInTheDocument();
    expect(screen.getByText('Transportadora nao encontrada')).toBeInTheDocument();
  });

  it('renders status badges with expected status codes', () => {
    render(
      <ScenarioPanel scenarios={mockScenarios} onSelect={vi.fn()} selectedId={null} />
    );
    expect(screen.getByText('201')).toBeInTheDocument();
    expect(screen.getByText('400')).toBeInTheDocument();
    // 422 appears twice (validation_error + cfop_error)
    expect(screen.getAllByText('422')).toHaveLength(2);
  });

  it('calls onSelect with scenario when card is clicked', () => {
    const onSelect = vi.fn();
    render(
      <ScenarioPanel scenarios={mockScenarios} onSelect={onSelect} selectedId={null} />
    );
    fireEvent.click(screen.getByText('Cenario feliz'));
    expect(onSelect).toHaveBeenCalledWith(mockScenarios[0]);
  });

  it('highlights the selected scenario card', () => {
    render(
      <ScenarioPanel
        scenarios={mockScenarios}
        onSelect={vi.fn()}
        selectedId="happy-path"
      />
    );
    const card = screen.getByText('Cenario feliz').closest('div.rounded-lg');
    expect(card?.className).toMatch(/ring/);
  });

  it('hides category with no scenarios', () => {
    const onlySuccess: Scenario[] = [mockScenarios[0]];
    render(
      <ScenarioPanel scenarios={onlySuccess} onSelect={vi.fn()} selectedId={null} />
    );
    expect(screen.getByText(/Sucesso/)).toBeInTheDocument();
    expect(screen.queryByText(/Erro de Negocio/)).not.toBeInTheDocument();
  });
});
