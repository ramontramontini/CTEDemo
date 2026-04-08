import { render, screen } from '@testing-library/react';
import { CteList } from '@/pages/Cte/components/CteList';

const MOCK_CTES = [
  {
    id: '1',
    cTeKey: '26251010758386000159570200000000011000000060',
    formattedAccessKey: '26 2510 10758386000159 57 020 000000001 1 00000006 0',
    freightOrderNumber: '12345678901234',
    status: 'Generated',
    erp: 'SAP',
    documentType: 'CT-e',
    totalFolders: 1,
    xml: '<?xml/>',
    createdAt: '2026-04-07T19:59:15',
    updatedAt: '2026-04-07T19:59:15',
  },
  {
    id: '2',
    cTeKey: '26251010758386000159570200000000021000000071',
    formattedAccessKey: '26 2510 10758386000159 57 020 000000002 1 00000007 1',
    freightOrderNumber: '98765432101234',
    status: 'Generated',
    erp: 'SAP',
    documentType: 'CT-e',
    totalFolders: 2,
    xml: '<?xml/>',
    createdAt: '2026-04-07T19:58:00',
    updatedAt: '2026-04-07T19:58:00',
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
    const badges = screen.getAllByText(/generated/i);
    expect(badges.length).toBe(2);
  });
});
