import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import { TransportadoraPage } from '@/pages/Transportadora/TransportadoraPage';

const mockTransportadoras = [
  {
    id: '1',
    cnpj: '11222333000181',
    razao_social: 'Transportadora ABC Ltda',
    nome_fantasia: 'ABC',
    ie: '123',
    uf: 'SP',
    cidade: 'Sao Paulo',
    logradouro: 'Rua A',
    numero: '100',
    bairro: 'Centro',
    cep: '01001000',
    status: 'active',
    created_at: '2026-01-01T00:00:00Z',
    updated_at: null,
  },
];

vi.mock('@/api/hooks/useTransportadoras', () => ({
  useTransportadoras: vi.fn(() => ({
    data: mockTransportadoras,
    isLoading: false,
    error: null,
  })),
  useCreateTransportadora: vi.fn(() => ({
    mutate: vi.fn(),
    isPending: false,
  })),
  useUpdateTransportadora: vi.fn(() => ({
    mutate: vi.fn(),
    isPending: false,
  })),
  useDeleteTransportadora: vi.fn(() => ({
    mutate: vi.fn(),
    isPending: false,
  })),
}));

function renderPage() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return render(
    <QueryClientProvider client={queryClient}>
      <TransportadoraPage />
    </QueryClientProvider>,
  );
}

describe('TransportadoraPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders transportadora list with table columns', () => {
    renderPage();
    expect(screen.getByText('Transportadoras')).toBeInTheDocument();
    expect(screen.getByText('CNPJ')).toBeInTheDocument();
    expect(screen.getByText('Razao Social')).toBeInTheDocument();
    expect(screen.getByText('UF')).toBeInTheDocument();
    expect(screen.getByText('Transportadora ABC Ltda')).toBeInTheDocument();
    expect(screen.getByText('SP')).toBeInTheDocument();
  });

  it('renders formatted CNPJ in list', () => {
    renderPage();
    expect(screen.getByText('11.222.333/0001-81')).toBeInTheDocument();
  });

  it('shows create form when Nova Transportadora clicked', async () => {
    renderPage();
    const user = userEvent.setup();
    await user.click(screen.getByText('Nova Transportadora'));
    expect(screen.getByText('Nova Transportadora', { selector: 'h2' })).toBeInTheDocument();
    expect(screen.getByText('Salvar')).toBeInTheDocument();
  });

  it('shows edit form when Editar clicked', async () => {
    renderPage();
    const user = userEvent.setup();
    await user.click(screen.getByText('Editar'));
    expect(screen.getByText('Editar Transportadora')).toBeInTheDocument();
  });
});
