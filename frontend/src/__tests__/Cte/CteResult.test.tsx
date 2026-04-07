import { render, screen, fireEvent } from '@testing-library/react';
import { CteResult } from '@/pages/Cte/components/CteResult';

const MOCK_CTE = {
  id: '550e8400-e29b-41d4-a716-446655440000',
  access_key: '26251010758386000159570200000000011000000060',
  formatted_access_key: '26 2510 10758386000159 57 020 000000001 1 00000006 0',
  freight_order_number: '12345678901234',
  status: 'gerado',
  xml: '<?xml version="1.0"?><CTe><infCte></infCte></CTe>',
  created_at: '2026-04-07T19:59:15',
};

describe('CteResult', () => {
  it('renders access key', () => {
    render(<CteResult cte={MOCK_CTE} />);
    expect(screen.getByText(/chave/i)).toBeInTheDocument();
    expect(screen.getByText(/26 2510 1075/)).toBeInTheDocument();
  });

  it('renders status badge as GERADO', () => {
    render(<CteResult cte={MOCK_CTE} />);
    expect(screen.getByText(/gerado/i)).toBeInTheDocument();
  });

  it('renders creation timestamp', () => {
    render(<CteResult cte={MOCK_CTE} />);
    expect(screen.getByText(/2026/)).toBeInTheDocument();
  });

  it('shows XML preview on toggle', () => {
    render(<CteResult cte={MOCK_CTE} />);
    const toggle = screen.getByRole('button', { name: /ver xml/i });
    fireEvent.click(toggle);
    expect(screen.getByText(/<CTe>/)).toBeInTheDocument();
  });
});
