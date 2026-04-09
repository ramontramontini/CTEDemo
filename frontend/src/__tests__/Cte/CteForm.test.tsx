import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { CteForm } from '@/pages/Cte/components/CteForm';
import { describe, it, expect, vi, beforeEach } from 'vitest';

function wrapper({ children }: { children: React.ReactNode }) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return <QueryClientProvider client={qc}>{children}</QueryClientProvider>;
}

describe('CteForm', () => {
  const onSubmit = vi.fn();
  const defaultProps = { onSubmit, isLoading: false, errors: null };

  beforeEach(() => {
    onSubmit.mockReset();
  });

  it('renders textarea and buttons', () => {
    render(<CteForm {...defaultProps} />, { wrapper });
    expect(screen.getByRole('textbox')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /gerar ct-e/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /exemplo json/i })).toBeInTheDocument();
  });

  it('disables submit when textarea is empty', () => {
    render(<CteForm {...defaultProps} />, { wrapper });
    expect(screen.getByRole('button', { name: /gerar ct-e/i })).toBeDisabled();
  });

  it('populates sample JSON on Exemplo click', () => {
    render(<CteForm {...defaultProps} />, { wrapper });
    fireEvent.click(screen.getByRole('button', { name: /exemplo json/i }));
    const textarea = screen.getByRole('textbox') as HTMLTextAreaElement;
    expect(textarea.value).toContain('FreightOrder');
    expect(textarea.value).toContain('Carrier');
  });

  it('calls onSubmit with parsed JSON on form submit', async () => {
    render(<CteForm {...defaultProps} />, { wrapper });
    const textarea = screen.getByRole('textbox');
    fireEvent.change(textarea, { target: { value: '{"FreightOrder":"123"}' } });
    fireEvent.click(screen.getByRole('button', { name: /gerar ct-e/i }));
    await waitFor(() => {
      expect(onSubmit).toHaveBeenCalledWith({ FreightOrder: '123' });
    });
  });

  it('shows JSON syntax error for malformed input', () => {
    render(<CteForm {...defaultProps} />, { wrapper });
    const textarea = screen.getByRole('textbox');
    fireEvent.change(textarea, { target: { value: '{bad json' } });
    fireEvent.click(screen.getByRole('button', { name: /gerar ct-e/i }));
    expect(screen.getByText(/json inválido/i)).toBeInTheDocument();
    expect(onSubmit).not.toHaveBeenCalled();
  });

  it('shows loading state on button when isLoading', () => {
    render(<CteForm {...{ ...defaultProps, isLoading: true }} />, { wrapper });
    expect(screen.getByRole('button', { name: /gerando/i })).toBeDisabled();
  });

  it('shows expected outcome info bar when expectedOutcome is provided', () => {
    render(
      <CteForm {...defaultProps} expectedOutcome="201 — CT-e gerado com sucesso" />,
      { wrapper },
    );
    expect(screen.getByTestId('expected-outcome')).toHaveTextContent(
      'Esperado: 201 — CT-e gerado com sucesso',
    );
  });

  it('does not show info bar when expectedOutcome is null', () => {
    render(<CteForm {...defaultProps} expectedOutcome={null} />, { wrapper });
    expect(screen.queryByTestId('expected-outcome')).not.toBeInTheDocument();
  });

  it('loads external JSON into textarea when externalJson changes', () => {
    const { rerender } = render(<CteForm {...defaultProps} />, { wrapper });
    rerender(
      <QueryClientProvider client={new QueryClient({ defaultOptions: { queries: { retry: false } } })}>
        <CteForm {...defaultProps} externalJson='{"FreightOrder":"EXT"}' />
      </QueryClientProvider>,
    );
    const textarea = screen.getByRole('textbox') as HTMLTextAreaElement;
    expect(textarea.value).toContain('EXT');
  });
});
