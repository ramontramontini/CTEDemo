import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MemoryRouter } from 'react-router-dom';
import { AppShell } from '@/components/layout/AppShell';

vi.mock('@/api/apiService', () => ({
  api: {
    resetData: vi.fn(),
  },
}));

import { api } from '@/api/apiService';

function renderShell() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter>
        <AppShell>
          <div>content</div>
        </AppShell>
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

describe('Reset Button', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders Limpar Dados button in navbar', () => {
    renderShell();
    expect(screen.getByText('Limpar Dados')).toBeInTheDocument();
  });

  it('calls resetData API on click', async () => {
    (api.resetData as ReturnType<typeof vi.fn>).mockResolvedValue({ status: 'ok' });
    renderShell();
    fireEvent.click(screen.getByText('Limpar Dados'));
    await waitFor(() => {
      expect(api.resetData).toHaveBeenCalledTimes(1);
    });
  });

  it('shows success feedback after reset', async () => {
    (api.resetData as ReturnType<typeof vi.fn>).mockResolvedValue({ status: 'ok' });
    renderShell();
    fireEvent.click(screen.getByText('Limpar Dados'));
    await waitFor(() => {
      expect(screen.getByText('Dados resetados')).toBeInTheDocument();
    });
  });
});
