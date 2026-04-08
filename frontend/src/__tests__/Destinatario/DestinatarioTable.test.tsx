import { render, screen } from '@testing-library/react';
import { DestinatarioTable } from '@/pages/Destinatario/components/DestinatarioTable';
import type { Destinatario } from '@/types';

const MOCK_DESTINATARIOS: Destinatario[] = [
  {
    id: '1',
    cnpj: '11222333000181',
    cpf: null,
    razao_social: 'Comercio Recife Ltda',
    nome_fantasia: 'Recife Com',
    ie: '123456789',
    uf: 'PE',
    cidade: 'Recife',
    logradouro: 'Rua do Sol',
    numero: '50',
    bairro: 'Boa Vista',
    cep: '50060000',
    status: 'active',
    created_at: '2026-04-07T20:00:00',
    updated_at: null,
  },
  {
    id: '2',
    cnpj: null,
    cpf: '12345678909',
    razao_social: 'Maria Silva',
    nome_fantasia: '',
    ie: '',
    uf: 'SP',
    cidade: 'Sao Paulo',
    logradouro: 'Av Paulista',
    numero: '1000',
    bairro: 'Bela Vista',
    cep: '01310100',
    status: 'active',
    created_at: '2026-04-07T19:00:00',
    updated_at: null,
  },
];

describe('DestinatarioTable', () => {
  it('renders empty state when no destinatarios', () => {
    render(<DestinatarioTable destinatarios={[]} onEdit={() => {}} onDelete={() => {}} />);
    expect(screen.getByText(/nenhum destinat.rio/i)).toBeInTheDocument();
  });

  it('renders CNPJ/CPF column', () => {
    render(<DestinatarioTable destinatarios={MOCK_DESTINATARIOS} onEdit={() => {}} onDelete={() => {}} />);
    expect(screen.getByText('11222333000181')).toBeInTheDocument();
    expect(screen.getByText('12345678909')).toBeInTheDocument();
  });

  it('renders Razao Social column', () => {
    render(<DestinatarioTable destinatarios={MOCK_DESTINATARIOS} onEdit={() => {}} onDelete={() => {}} />);
    expect(screen.getByText('Comercio Recife Ltda')).toBeInTheDocument();
    expect(screen.getByText('Maria Silva')).toBeInTheDocument();
  });

  it('renders UF and Cidade columns', () => {
    render(<DestinatarioTable destinatarios={MOCK_DESTINATARIOS} onEdit={() => {}} onDelete={() => {}} />);
    expect(screen.getByText('PE')).toBeInTheDocument();
    expect(screen.getByText('SP')).toBeInTheDocument();
    expect(screen.getByText('Recife')).toBeInTheDocument();
    expect(screen.getByText('Sao Paulo')).toBeInTheDocument();
  });

  it('renders edit and delete buttons for each row', () => {
    render(<DestinatarioTable destinatarios={MOCK_DESTINATARIOS} onEdit={() => {}} onDelete={() => {}} />);
    const editButtons = screen.getAllByRole('button', { name: /editar/i });
    const deleteButtons = screen.getAllByRole('button', { name: /excluir/i });
    expect(editButtons).toHaveLength(2);
    expect(deleteButtons).toHaveLength(2);
  });
});
