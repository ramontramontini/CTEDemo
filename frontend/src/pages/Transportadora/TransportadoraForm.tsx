import { useState } from 'react';
import type { CreateTransportadoraRequest, Transportadora } from '@/types';

interface TransportadoraFormProps {
  initial?: Transportadora;
  onSubmit: (data: CreateTransportadoraRequest) => void;
  onCancel: () => void;
  isLoading: boolean;
  error?: string | null;
}

const EMPTY_FORM: CreateTransportadoraRequest = {
  cnpj: '',
  razao_social: '',
  nome_fantasia: '',
  ie: '',
  uf: '',
  cidade: '',
  logradouro: '',
  numero: '',
  bairro: '',
  cep: '',
};

export function TransportadoraForm({ initial, onSubmit, onCancel, isLoading, error }: TransportadoraFormProps) {
  const [form, setForm] = useState<CreateTransportadoraRequest>(
    initial
      ? {
          cnpj: initial.cnpj,
          razao_social: initial.razao_social,
          nome_fantasia: initial.nome_fantasia,
          ie: initial.ie,
          uf: initial.uf,
          cidade: initial.cidade,
          logradouro: initial.logradouro,
          numero: initial.numero,
          bairro: initial.bairro,
          cep: initial.cep,
        }
      : EMPTY_FORM,
  );

  const handleChange = (field: keyof CreateTransportadoraRequest, value: string) => {
    setForm((prev) => ({ ...prev, [field]: value }));
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit(form);
  };

  return (
    <form onSubmit={handleSubmit} className="bg-white p-6 rounded-lg shadow space-y-4">
      <h2 className="text-lg font-semibold text-gray-900">
        {initial ? 'Editar Transportadora' : 'Nova Transportadora'}
      </h2>
      {error && <p className="text-red-600 text-sm">{error}</p>}
      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-700">CNPJ *</label>
          <input
            type="text"
            value={form.cnpj}
            onChange={(e) => handleChange('cnpj', e.target.value)}
            className="mt-1 block w-full rounded border-gray-300 shadow-sm text-sm"
            required
            maxLength={18}
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700">Razao Social *</label>
          <input
            type="text"
            value={form.razao_social}
            onChange={(e) => handleChange('razao_social', e.target.value)}
            className="mt-1 block w-full rounded border-gray-300 shadow-sm text-sm"
            required
            maxLength={150}
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700">Nome Fantasia</label>
          <input
            type="text"
            value={form.nome_fantasia ?? ''}
            onChange={(e) => handleChange('nome_fantasia', e.target.value)}
            className="mt-1 block w-full rounded border-gray-300 shadow-sm text-sm"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700">IE</label>
          <input
            type="text"
            value={form.ie ?? ''}
            onChange={(e) => handleChange('ie', e.target.value)}
            className="mt-1 block w-full rounded border-gray-300 shadow-sm text-sm"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700">UF *</label>
          <input
            type="text"
            value={form.uf}
            onChange={(e) => handleChange('uf', e.target.value.toUpperCase())}
            className="mt-1 block w-full rounded border-gray-300 shadow-sm text-sm"
            required
            maxLength={2}
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700">Cidade *</label>
          <input
            type="text"
            value={form.cidade}
            onChange={(e) => handleChange('cidade', e.target.value)}
            className="mt-1 block w-full rounded border-gray-300 shadow-sm text-sm"
            required
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700">Logradouro *</label>
          <input
            type="text"
            value={form.logradouro}
            onChange={(e) => handleChange('logradouro', e.target.value)}
            className="mt-1 block w-full rounded border-gray-300 shadow-sm text-sm"
            required
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700">Numero *</label>
          <input
            type="text"
            value={form.numero}
            onChange={(e) => handleChange('numero', e.target.value)}
            className="mt-1 block w-full rounded border-gray-300 shadow-sm text-sm"
            required
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700">Bairro *</label>
          <input
            type="text"
            value={form.bairro}
            onChange={(e) => handleChange('bairro', e.target.value)}
            className="mt-1 block w-full rounded border-gray-300 shadow-sm text-sm"
            required
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700">CEP *</label>
          <input
            type="text"
            value={form.cep}
            onChange={(e) => handleChange('cep', e.target.value)}
            className="mt-1 block w-full rounded border-gray-300 shadow-sm text-sm"
            required
            maxLength={8}
          />
        </div>
      </div>
      <div className="flex justify-end gap-3 pt-2">
        <button
          type="button"
          onClick={onCancel}
          className="px-4 py-2 text-sm text-gray-700 bg-gray-100 rounded hover:bg-gray-200"
        >
          Cancelar
        </button>
        <button
          type="submit"
          disabled={isLoading}
          className="px-4 py-2 text-sm text-white bg-blue-600 rounded hover:bg-blue-700 disabled:opacity-50"
        >
          {isLoading ? 'Salvando...' : 'Salvar'}
        </button>
      </div>
    </form>
  );
}
