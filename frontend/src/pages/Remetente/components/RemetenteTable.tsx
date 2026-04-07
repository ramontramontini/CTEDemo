import type { Remetente } from '@/types';

interface RemetenteTableProps {
  remetentes: Remetente[];
  onEdit: (remetente: Remetente) => void;
  onDelete: (id: string) => void;
}

export function RemetenteTable({ remetentes, onEdit, onDelete }: RemetenteTableProps) {
  if (remetentes.length === 0) {
    return <p className="text-gray-500">Nenhum remetente cadastrado.</p>;
  }

  return (
    <div className="overflow-x-auto">
      <table className="min-w-full divide-y divide-gray-200">
        <thead className="bg-gray-50">
          <tr>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">CNPJ</th>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Razao Social</th>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">UF</th>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Cidade</th>
            <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">Acoes</th>
          </tr>
        </thead>
        <tbody className="bg-white divide-y divide-gray-200">
          {remetentes.map((r) => (
            <tr key={r.id}>
              <td className="px-4 py-3 whitespace-nowrap text-sm">{r.cnpj}</td>
              <td className="px-4 py-3 whitespace-nowrap text-sm">{r.razao_social}</td>
              <td className="px-4 py-3 whitespace-nowrap text-sm">{r.uf}</td>
              <td className="px-4 py-3 whitespace-nowrap text-sm">{r.cidade}</td>
              <td className="px-4 py-3 whitespace-nowrap text-sm text-right space-x-2">
                <button
                  onClick={() => onEdit(r)}
                  className="text-indigo-600 hover:text-indigo-900"
                  aria-label="Editar"
                >
                  Editar
                </button>
                <button
                  onClick={() => onDelete(r.id)}
                  className="text-red-600 hover:text-red-900"
                  aria-label="Excluir"
                >
                  Excluir
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
