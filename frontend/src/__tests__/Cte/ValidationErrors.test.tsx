import { render, screen } from '@testing-library/react';
import { ValidationErrors } from '@/pages/Cte/components/ValidationErrors';

describe('ValidationErrors', () => {
  it('renders nothing when errors is null', () => {
    const { container } = render(<ValidationErrors errors={null} />);
    expect(container.firstChild).toBeNull();
  });

  it('renders nothing when errors is empty', () => {
    const { container } = render(<ValidationErrors errors={{}} />);
    expect(container.firstChild).toBeNull();
  });

  it('renders error list from errors dict', () => {
    const errors = {
      Carrier: 'CNPJ inválido — dígito verificador incorreto',
      'Folder[0].DriverID': 'CPF inválido — sequência repetida',
    };
    render(<ValidationErrors errors={errors} />);
    expect(screen.getByText(/CNPJ inválido/)).toBeInTheDocument();
    expect(screen.getByText(/CPF inválido/)).toBeInTheDocument();
  });
});
