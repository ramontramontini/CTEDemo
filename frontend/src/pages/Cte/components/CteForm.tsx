import { useState } from 'react';
import type { ValidationError } from '@/types';
import { SAMPLE_PAYLOAD } from '../samplePayload';

interface CteFormProps {
  onSubmit: (payload: Record<string, unknown>) => void;
  isLoading: boolean;
  errors: ValidationError[] | null;
}

export function CteForm({ onSubmit, isLoading, errors }: CteFormProps) {
  const [json, setJson] = useState('');
  const [parseError, setParseError] = useState<string | null>(null);

  const handleSubmit = () => {
    setParseError(null);
    try {
      const parsed = JSON.parse(json);
      onSubmit(parsed);
    } catch {
      setParseError('JSON inválido — verifique a sintaxe');
    }
  };

  const handleSample = () => {
    setJson(JSON.stringify(SAMPLE_PAYLOAD, null, 2));
    setParseError(null);
  };

  const isEmpty = json.trim() === '';

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h2 className="text-xl font-semibold text-gray-900 mb-4">Gerar CT-e</h2>
      <textarea
        className="w-full h-64 font-mono text-sm border border-gray-300 rounded-md p-3 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
        value={json}
        onChange={(e) => setJson(e.target.value)}
        placeholder="Cole o JSON do pedido de frete aqui..."
      />
      {parseError && (
        <p className="mt-2 text-sm text-red-600">{parseError}</p>
      )}
      <div className="mt-4 flex justify-between">
        <button
          type="button"
          onClick={handleSample}
          className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 rounded-md hover:bg-gray-200"
        >
          Exemplo JSON
        </button>
        <button
          type="button"
          onClick={handleSubmit}
          disabled={isEmpty || isLoading}
          className="px-6 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isLoading ? 'Gerando...' : 'Gerar CT-e'}
        </button>
      </div>
    </div>
  );
}
