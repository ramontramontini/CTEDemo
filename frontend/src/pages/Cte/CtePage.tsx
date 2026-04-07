import { useState } from 'react';
import { useCtes, useGenerateCte } from '@/api/hooks/useCtes';
import type { Cte, ValidationError } from '@/types';
import { CteForm } from './components/CteForm';
import { CteResult } from './components/CteResult';
import { CteList } from './components/CteList';
import { ValidationErrors } from './components/ValidationErrors';

export function CtePage() {
  const { data: ctes, isLoading: listLoading, error: listError } = useCtes();
  const generateMutation = useGenerateCte();
  const [lastResult, setLastResult] = useState<Cte | null>(null);
  const [validationErrors, setValidationErrors] = useState<ValidationError[] | null>(null);

  const handleSubmit = (payload: Record<string, unknown>) => {
    setValidationErrors(null);
    setLastResult(null);
    generateMutation.mutate(payload, {
      onSuccess: (data) => {
        setLastResult(data);
        setValidationErrors(null);
      },
      onError: (error) => {
        const errs = (error as unknown as Record<string, unknown>).validationErrors as ValidationError[] | undefined;
        if (errs) {
          setValidationErrors(errs);
        }
      },
    });
  };

  return (
    <div className="space-y-6">
      <CteForm
        onSubmit={handleSubmit}
        isLoading={generateMutation.isPending}
        errors={validationErrors}
      />

      {validationErrors && <ValidationErrors errors={validationErrors} />}

      {lastResult && <CteResult cte={lastResult} />}

      <div>
        <h2 className="text-xl font-semibold text-gray-900 mb-4">CT-es Gerados</h2>
        {listLoading ? (
          <p className="text-gray-500">Carregando...</p>
        ) : listError ? (
          <p className="text-red-500 text-sm">Erro ao carregar CT-es.</p>
        ) : (
          <CteList ctes={ctes || []} />
        )}
      </div>
    </div>
  );
}
