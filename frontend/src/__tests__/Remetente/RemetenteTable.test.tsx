import { render, screen } from '@testing-library/react';
import { RemetenteTable } from '@/pages/Remetente/components/RemetenteTable';
import type { Remetente } from '@/types';

const MOCK_REMETENTES: Remetente[] = [
  {
    id: '1',
    cnpj: '11222333000181',
    razao_social: 'Empresa ABC Ltda',
    nome_fantasia: 'ABC',
    ie: '123456789',
    uf: 'SP',
    cidade: 'Sao Paulo',
    logradouro: 'Rua A',
    numero: '100',
    bairro: 'Centro',
    cep: '01001000',
    status: 'active',
    created_at: '2026-04-07T20:00:00',
    updated_at: null,
  },
  {
    id: '2',
    cnpj: '11444777000161',
    razao_social: 'Industria XYZ SA',
    nome_fantasia: 'XYZ',
    ie: '987654321',
    uf: 'RJ',
    cidade: 'Rio de Janeiro',
    logradouro: 'Av B',
    numero: '200',
    bairro: 'Botafogo',
    cep: '22041080',
    status: 'active',
    created_at: '2026-04-07T19:00:00',
    updated_at: null,
  },
];

describe('RemetenteTable', () => {
  it('renders empty state when no remetentes', () => {
    render(<RemetenteTable remetentes={[]} onEdit={() => {}} onDelete={() => {}} />);
    expect(screen.getByText(/nenhum remetente/i)).toBeInTheDocument();
  });

  it('renders table with CNPJ column', () => {
    render(<RemetenteTable remetentes={MOCK_REMETENTES} onEdit={() => {}} onDelete={() => {}} />);
    expect(screen.getByText('11222333000181')).toBeInTheDocument();
    expect(screen.getByText('11444777000161')).toBeInTheDocument();
  });

  it('renders Razao Social column', () => {
    render(<RemetenteTable remetentes={MOCK_REMETENTES} onEdit={() => {}} onDelete={() => {}} />);
    expect(screen.getByText('Empresa ABC Ltda')).toBeInTheDocument();
    expect(screen.getByText('Industria XYZ SA')).toBeInTheDocument();
  });

  it('renders UF and Cidade columns', () => {
    render(<RemetenteTable remetentes={MOCK_REMETENTES} onEdit={() => {}} onDelete={() => {}} />);
    expect(screen.getByText('SP')).toBeInTheDocument();
    expect(screen.getByText('RJ')).toBeInTheDocument();
    expect(screen.getByText('Sao Paulo')).toBeInTheDocument();
    expect(screen.getByText('Rio de Janeiro')).toBeInTheDocument();
  });

  it('renders edit and delete buttons for each row', () => {
    render(<RemetenteTable remetentes={MOCK_REMETENTES} onEdit={() => {}} onDelete={() => {}} />);
    const editButtons = screen.getAllByRole('button', { name: /editar/i });
    const deleteButtons = screen.getAllByRole('button', { name: /excluir/i });
    expect(editButtons).toHaveLength(2);
    expect(deleteButtons).toHaveLength(2);
  });
});
