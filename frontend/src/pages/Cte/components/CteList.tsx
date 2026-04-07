import type { Cte } from '@/types';

interface CteListProps {
  ctes: Cte[];
}

export function CteList({ ctes }: CteListProps) {
  if (ctes.length === 0) {
    return <p className="text-gray-500 text-sm">Nenhum CT-e gerado ainda.</p>;
  }

  return (
    <div className="space-y-2">
      {ctes.map((cte) => (
        <div
          key={cte.id}
          className="bg-white rounded-lg shadow p-4 flex items-center justify-between"
        >
          <div className="space-y-1">
            <p className="font-mono text-sm text-gray-800">
              {cte.formatted_access_key}
            </p>
            <div className="flex items-center gap-3 text-xs text-gray-500">
              <span className="inline-flex items-center px-2 py-0.5 rounded-full font-medium bg-green-100 text-green-800 uppercase">
                {cte.status}
              </span>
              <span>Pedido: {cte.freight_order_number}</span>
              <span>{new Date(cte.created_at).toLocaleTimeString('pt-BR')}</span>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}
