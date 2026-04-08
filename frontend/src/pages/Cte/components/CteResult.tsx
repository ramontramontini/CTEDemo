import { useState } from 'react';
import type { Cte } from '@/types';

interface CteResultProps {
  cte: Cte;
}

export function CteResult({ cte }: CteResultProps) {
  const [showXml, setShowXml] = useState(false);

  return (
    <div className="bg-white rounded-lg shadow p-6 border-l-4 border-green-500">
      <div className="flex items-center gap-2 mb-3">
        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800 uppercase">
          {cte.status}
        </span>
      </div>
      <div className="space-y-2 text-sm text-gray-700">
        <p>
          <span className="font-medium">Chave:</span>{' '}
          <span className="font-mono">{cte.formattedAccessKey}</span>
        </p>
        <p>
          <span className="font-medium">Criado em:</span>{' '}
          {new Date(cte.createdAt).toLocaleString('pt-BR')}
        </p>
      </div>
      <div className="mt-4">
        <button
          type="button"
          onClick={() => setShowXml(!showXml)}
          className="text-sm text-blue-600 hover:text-blue-800 font-medium"
        >
          {showXml ? 'Ocultar XML' : 'Ver XML'}
        </button>
        {showXml && (
          <pre className="mt-2 p-3 bg-gray-50 rounded-md text-xs font-mono overflow-x-auto max-h-64 overflow-y-auto">
            {cte.xml}
          </pre>
        )}
      </div>
    </div>
  );
}
