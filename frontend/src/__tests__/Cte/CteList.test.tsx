import { render, screen } from '@testing-library/react';
import { CteList } from '@/pages/Cte/components/CteList';

const MOCK_CTES = [
  {
    id: '1',
    access_key: '26251010758386000159570200000000011000000060',
    formatted_access_key: '26 2510 10758386000159 57 020 000000001 1 00000006 0',
    freight_order_number: '12345678901234',
    status: 'gerado',
    xml: '<?xml/>',
    created_at: '2026-04-07T19:59:15',
  },
  {
    id: '2',
    access_key: '26251010758386000159570200000000021000000071',
    formatted_access_key: '26 2510 10758386000159 57 020 000000002 1 00000007 1',
    freight_order_number: '98765432101234',
    status: 'gerado',
    xml: '<?xml/>',
    created_at: '2026-04-07T19:58:00',
  },
];

describe('CteList', () => {
  it('renders empty state message', () => {
    render(<CteList ctes={[]} />);
    expect(screen.getByText(/nenhum ct-e gerado/i)).toBeInTheDocument();
  });

  it('renders list of CT-es', () => {
    render(<CteList ctes={MOCK_CTES} />);
    expect(screen.getByText(/12345678901234/)).toBeInTheDocument();
    expect(screen.getByText(/98765432101234/)).toBeInTheDocument();
  });

  it('shows status badge for each item', () => {
    render(<CteList ctes={MOCK_CTES} />);
    const badges = screen.getAllByText(/gerado/i);
    expect(badges.length).toBe(2);
  });
});
