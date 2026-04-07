import { render, screen } from '@testing-library/react';
import { ValidationErrors } from '@/pages/Cte/components/ValidationErrors';

describe('ValidationErrors', () => {
  it('renders nothing when errors is null', () => {
    const { container } = render(<ValidationErrors errors={null} />);
    expect(container.firstChild).toBeNull();
  });

  it('renders nothing when errors is empty', () => {
    const { container } = render(<ValidationErrors errors={[]} />);
    expect(container.firstChild).toBeNull();
  });

  it('renders error list with field and message', () => {
    const errors = [
      { field: 'Carrier', message: 'CNPJ inválido — dígito verificador incorreto' },
      { field: 'Folder[0].DriverID', message: 'CPF inválido — sequência repetida' },
    ];
    render(<ValidationErrors errors={errors} />);
    expect(screen.getByText(/CNPJ inválido/)).toBeInTheDocument();
    expect(screen.getByText(/CPF inválido/)).toBeInTheDocument();
  });
});
