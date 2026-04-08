import { render, screen, fireEvent } from '@testing-library/react';
import { DestinatarioForm } from '@/pages/Destinatario/components/DestinatarioForm';

describe('DestinatarioForm', () => {
  it('renders PJ fields by default', () => {
    render(<DestinatarioForm onSubmit={() => {}} onCancel={() => {}} />);
    expect(screen.getByLabelText(/cnpj/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/raz.o social/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/nome fantasia/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/^ie$/i)).toBeInTheDocument();
  });

  it('toggles to PF mode and shows CPF field', () => {
    render(<DestinatarioForm onSubmit={() => {}} onCancel={() => {}} />);
    fireEvent.click(screen.getByLabelText(/^pf$/i));
    expect(screen.getByLabelText(/cpf/i)).toBeInTheDocument();
    expect(screen.queryByLabelText(/cnpj/i)).not.toBeInTheDocument();
    expect(screen.queryByLabelText(/nome fantasia/i)).not.toBeInTheDocument();
    expect(screen.queryByLabelText(/^ie$/i)).not.toBeInTheDocument();
  });

  it('renders address fields in both modes', () => {
    render(<DestinatarioForm onSubmit={() => {}} onCancel={() => {}} />);
    expect(screen.getByLabelText(/uf/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/cidade/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/logradouro/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/n.mero/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/bairro/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/cep/i)).toBeInTheDocument();
  });

  it('renders submit and cancel buttons', () => {
    render(<DestinatarioForm onSubmit={() => {}} onCancel={() => {}} />);
    expect(screen.getByRole('button', { name: /salvar/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /cancelar/i })).toBeInTheDocument();
  });

  it('pre-fills fields when editing PJ', () => {
    const initial = {
      cnpj: '11222333000181',
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
    render(<DestinatarioForm onSubmit={() => {}} onCancel={() => {}} initialData={initial} isEdit />);
    expect(screen.getByDisplayValue('Test Corp')).toBeInTheDocument();
    expect(screen.getByDisplayValue('SP')).toBeInTheDocument();
  });

  it('disables PJ/PF toggle when editing', () => {
    const initial = {
      cnpj: '11222333000181',
      razao_social: 'Test Corp',
      uf: 'SP',
      cidade: 'SP',
      logradouro: 'Rua',
      numero: '1',
      bairro: 'B',
      cep: '01001000',
    };
    render(<DestinatarioForm onSubmit={() => {}} onCancel={() => {}} initialData={initial} isEdit />);
    expect(screen.getByLabelText(/^pj$/i)).toBeDisabled();
    expect(screen.getByLabelText(/^pf$/i)).toBeDisabled();
  });
});
