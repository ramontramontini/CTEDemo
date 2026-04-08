import { useState } from 'react';
import { useRemetentes, useCreateRemetente, useUpdateRemetente, useDeleteRemetente } from '@/api/hooks/useRemetentes';
import { extractErrorMessage } from '@/api/errorUtils';
import { RemetenteTable } from './components/RemetenteTable';
import { RemetenteForm } from './components/RemetenteForm';
import type { Remetente, CreateRemetenteRequest, UpdateRemetenteRequest } from '@/types';

type FormMode = { kind: 'closed' } | { kind: 'create' } | { kind: 'edit'; remetente: Remetente };

export function RemetentePage() {
  const { data: items, isLoading, error } = useRemetentes();
  const createMutation = useCreateRemetente();
  const updateMutation = useUpdateRemetente();
  const deleteMutation = useDeleteRemetente();
  const [formMode, setFormMode] = useState<FormMode>({ kind: 'closed' });
  const [formError, setFormError] = useState<string | null>(null);

  if (isLoading) return <div className="text-gray-500">Carregando...</div>;
  if (error) return <div className="text-red-500">Erro ao carregar remetentes: {extractErrorMessage(error)}</div>;

  function handleCreate(data: CreateRemetenteRequest | UpdateRemetenteRequest) {
    setFormError(null);
    createMutation.mutate(data as CreateRemetenteRequest, {
      onSuccess: () => setFormMode({ kind: 'closed' }),
      onError: (err) => setFormError(extractErrorMessage(err)),
    });
  }

  function handleUpdate(data: CreateRemetenteRequest | UpdateRemetenteRequest) {
    if (formMode.kind !== 'edit') return;
    setFormError(null);
    updateMutation.mutate({ id: formMode.remetente.id, data: data as UpdateRemetenteRequest }, {
      onSuccess: () => setFormMode({ kind: 'closed' }),
      onError: (err) => setFormError(extractErrorMessage(err)),
    });
  }

  function handleDelete(id: string) {
    if (!window.confirm('Excluir este remetente?')) return;
    deleteMutation.mutate(id);
  }

  function handleEdit(remetente: Remetente) {
    setFormError(null);
    setFormMode({ kind: 'edit', remetente });
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <h1 className="text-2xl font-bold text-gray-900">Remetentes</h1>
        {formMode.kind === 'closed' && (
          <button
            onClick={() => { setFormError(null); setFormMode({ kind: 'create' }); }}
            className="rounded-md bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700"
          >
            + Novo Remetente
          </button>
        )}
      </div>

      {formMode.kind !== 'closed' && (
        <div className="bg-white p-6 rounded-lg shadow mb-6">
          <h2 className="text-lg font-semibold mb-4">
            {formMode.kind === 'create' ? 'Novo Remetente' : 'Editar Remetente'}
          </h2>
          <RemetenteForm
            onSubmit={formMode.kind === 'create' ? handleCreate : handleUpdate}
            onCancel={() => setFormMode({ kind: 'closed' })}
            initialData={formMode.kind === 'edit' ? formMode.remetente : undefined}
            isEdit={formMode.kind === 'edit'}
            error={formError}
          />
        </div>
      )}

      <RemetenteTable
        remetentes={items ?? []}
        onEdit={handleEdit}
        onDelete={handleDelete}
      />
    </div>
  );
}
