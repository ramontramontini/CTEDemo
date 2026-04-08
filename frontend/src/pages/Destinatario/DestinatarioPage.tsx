import { useState } from 'react';
import { useDestinatarios, useCreateDestinatario, useUpdateDestinatario, useDeleteDestinatario } from '@/api/hooks/useDestinatarios';
import { DestinatarioTable } from './components/DestinatarioTable';
import { DestinatarioForm } from './components/DestinatarioForm';
import type { Destinatario, CreateDestinatarioRequest, UpdateDestinatarioRequest } from '@/types';

type FormMode = { kind: 'closed' } | { kind: 'create' } | { kind: 'edit'; destinatario: Destinatario };

export function DestinatarioPage() {
  const { data: items, isLoading, error } = useDestinatarios();
  const createMutation = useCreateDestinatario();
  const updateMutation = useUpdateDestinatario();
  const deleteMutation = useDeleteDestinatario();
  const [formMode, setFormMode] = useState<FormMode>({ kind: 'closed' });
  const [formError, setFormError] = useState<string | null>(null);

  if (isLoading) return <div className="text-gray-500">Loading...</div>;
  if (error) return <div className="text-red-500">Error loading destinatarios</div>;

  function handleCreate(data: CreateDestinatarioRequest | UpdateDestinatarioRequest) {
    setFormError(null);
    createMutation.mutate(data as CreateDestinatarioRequest, {
      onSuccess: () => setFormMode({ kind: 'closed' }),
      onError: (err) => {
        const msg = (err as Record<string, unknown>).response
          ? ((err as Record<string, { data?: { detail?: string } }>).response?.data?.detail ?? 'Erro ao criar destinatario')
          : 'Erro ao criar destinatario';
        setFormError(String(msg));
      },
    });
  }

  function handleUpdate(data: CreateDestinatarioRequest | UpdateDestinatarioRequest) {
    if (formMode.kind !== 'edit') return;
    setFormError(null);
    updateMutation.mutate({ id: formMode.destinatario.id, data: data as UpdateDestinatarioRequest }, {
      onSuccess: () => setFormMode({ kind: 'closed' }),
      onError: (err) => {
        const msg = (err as Record<string, unknown>).response
          ? ((err as Record<string, { data?: { detail?: string } }>).response?.data?.detail ?? 'Erro ao atualizar destinatario')
          : 'Erro ao atualizar destinatario';
        setFormError(String(msg));
      },
    });
  }

  function handleDelete(id: string) {
    if (!window.confirm('Excluir este destinatario?')) return;
    deleteMutation.mutate(id);
  }

  function handleEdit(destinatario: Destinatario) {
    setFormError(null);
    setFormMode({ kind: 'edit', destinatario });
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <h1 className="text-2xl font-bold text-gray-900">Destinatarios</h1>
        {formMode.kind === 'closed' && (
          <button
            onClick={() => { setFormError(null); setFormMode({ kind: 'create' }); }}
            className="rounded-md bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700"
          >
            + Novo Destinatario
          </button>
        )}
      </div>

      {formMode.kind !== 'closed' && (
        <div className="bg-white p-6 rounded-lg shadow mb-6">
          <h2 className="text-lg font-semibold mb-4">
            {formMode.kind === 'create' ? 'Novo Destinatario' : 'Editar Destinatario'}
          </h2>
          <DestinatarioForm
            onSubmit={formMode.kind === 'create' ? handleCreate : handleUpdate}
            onCancel={() => setFormMode({ kind: 'closed' })}
            initialData={formMode.kind === 'edit' ? formMode.destinatario : undefined}
            isEdit={formMode.kind === 'edit'}
            error={formError}
          />
        </div>
      )}

      <DestinatarioTable
        destinatarios={items ?? []}
        onEdit={handleEdit}
        onDelete={handleDelete}
      />
    </div>
  );
}
