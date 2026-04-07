import { render, screen } from '@testing-library/react';
import { RemetenteForm } from '@/pages/Remetente/components/RemetenteForm';

describe('RemetenteForm', () => {
  it('renders all required fields', () => {
    render(<RemetenteForm onSubmit={() => {}} onCancel={() => {}} />);
    expect(screen.getByLabelText(/cnpj/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/raz.o social/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/uf/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/cidade/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/logradouro/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/n.mero/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/bairro/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/cep/i)).toBeInTheDocument();
  });

  it('renders optional fields', () => {
    render(<RemetenteForm onSubmit={() => {}} onCancel={() => {}} />);
    expect(screen.getByLabelText(/nome fantasia/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/^ie$/i)).toBeInTheDocument();
  });

  it('renders submit and cancel buttons', () => {
    render(<RemetenteForm onSubmit={() => {}} onCancel={() => {}} />);
    expect(screen.getByRole('button', { name: /salvar/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /cancelar/i })).toBeInTheDocument();
  });

  it('pre-fills fields when editing', () => {
    const initial = {
      razao_social: 'Test Corp',
      nome_fantasia: 'TC',
      ie: '12345',
      uf: 'SP',
      cidade: 'Sao Paulo',
      logradouro: 'Rua X',
      numero: '42',
      bairro: 'Centro',
      cep: '01001000',
    };
    render(<RemetenteForm onSubmit={() => {}} onCancel={() => {}} initialData={initial} />);
    expect(screen.getByDisplayValue('Test Corp')).toBeInTheDocument();
    expect(screen.getByDisplayValue('SP')).toBeInTheDocument();
  });
});
