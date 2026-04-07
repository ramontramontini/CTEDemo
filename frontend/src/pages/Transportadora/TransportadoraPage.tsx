import { useState } from 'react';
import {
  useTransportadoras,
  useCreateTransportadora,
  useUpdateTransportadora,
  useDeleteTransportadora,
} from '@/api/hooks/useTransportadoras';
import type { Transportadora, CreateTransportadoraRequest } from '@/types';
import { TransportadoraForm } from './TransportadoraForm';

type FormMode = { type: 'closed' } | { type: 'create' } | { type: 'edit'; item: Transportadora };

export function TransportadoraPage() {
  const { data: items, isLoading, error } = useTransportadoras();
  const createMutation = useCreateTransportadora();
  const updateMutation = useUpdateTransportadora();
  const deleteMutation = useDeleteTransportadora();
  const [formMode, setFormMode] = useState<FormMode>({ type: 'closed' });

  const handleCreate = (data: CreateTransportadoraRequest) => {
    createMutation.mutate(data, { onSuccess: () => setFormMode({ type: 'closed' }) });
  };

  const handleUpdate = (data: CreateTransportadoraRequest) => {
    if (formMode.type !== 'edit') return;
    updateMutation.mutate(
      { id: formMode.item.id, data },
      { onSuccess: () => setFormMode({ type: 'closed' }) },
    );
  };

  const handleDelete = (id: string) => {
    if (window.confirm('Confirmar exclusao?')) {
      deleteMutation.mutate(id);
    }
  };

  const formatCnpj = (cnpj: string) => {
    if (cnpj.length !== 14) return cnpj;
    return `${cnpj.slice(0, 2)}.${cnpj.slice(2, 5)}.${cnpj.slice(5, 8)}/${cnpj.slice(8, 12)}-${cnpj.slice(12)}`;
  };

  if (isLoading) return <div className="text-gray-500">Carregando...</div>;
  if (error) return <div className="text-red-500">Erro ao carregar transportadoras</div>;

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">Transportadoras</h1>
        {formMode.type === 'closed' && (
          <button
            onClick={() => setFormMode({ type: 'create' })}
            className="px-4 py-2 text-sm text-white bg-blue-600 rounded hover:bg-blue-700"
          >
            Nova Transportadora
          </button>
        )}
      </div>

      {formMode.type !== 'closed' && (
        <TransportadoraForm
          initial={formMode.type === 'edit' ? formMode.item : undefined}
          onSubmit={formMode.type === 'create' ? handleCreate : handleUpdate}
          onCancel={() => setFormMode({ type: 'closed' })}
          isLoading={createMutation.isPending || updateMutation.isPending}
        />
      )}

      {items && items.length > 0 ? (
        <div className="overflow-x-auto">
          <table className="min-w-full bg-white rounded-lg shadow">
            <thead>
              <tr className="bg-gray-50 text-left text-sm font-medium text-gray-500">
                <th className="px-4 py-3">CNPJ</th>
                <th className="px-4 py-3">Razao Social</th>
                <th className="px-4 py-3">UF</th>
                <th className="px-4 py-3">Status</th>
                <th className="px-4 py-3">Acoes</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {items.map((item) => (
                <tr key={item.id} className="text-sm text-gray-700">
                  <td className="px-4 py-3 font-mono">{formatCnpj(item.cnpj)}</td>
                  <td className="px-4 py-3">{item.razao_social}</td>
                  <td className="px-4 py-3">{item.uf}</td>
                  <td className="px-4 py-3">
                    <span className="px-2 py-1 text-xs rounded-full bg-green-100 text-green-800">
                      {item.status}
                    </span>
                  </td>
                  <td className="px-4 py-3 space-x-2">
                    <button
                      onClick={() => setFormMode({ type: 'edit', item })}
                      className="text-blue-600 hover:text-blue-800 text-xs"
                    >
                      Editar
                    </button>
                    <button
                      onClick={() => handleDelete(item.id)}
                      className="text-red-600 hover:text-red-800 text-xs"
                    >
                      Excluir
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <p className="text-gray-500">Nenhuma transportadora cadastrada.</p>
      )}
    </div>
  );
}
