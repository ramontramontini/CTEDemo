import type { Destinatario } from '@/types';

interface DestinatarioTableProps {
  destinatarios: Destinatario[];
  onEdit: (destinatario: Destinatario) => void;
  onDelete: (id: string) => void;
}

export function DestinatarioTable({ destinatarios, onEdit, onDelete }: DestinatarioTableProps) {
  if (destinatarios.length === 0) {
    return <p className="text-gray-500">Nenhum destinatário cadastrado.</p>;
  }

  return (
    <div className="overflow-x-auto">
      <table className="min-w-full divide-y divide-gray-200">
        <thead className="bg-gray-50">
          <tr>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">CNPJ/CPF</th>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Razao Social</th>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">UF</th>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Cidade</th>
            <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">Acoes</th>
          </tr>
        </thead>
        <tbody className="bg-white divide-y divide-gray-200">
          {destinatarios.map((d) => (
            <tr key={d.id}>
              <td className="px-4 py-3 whitespace-nowrap text-sm">{d.cnpj ?? d.cpf}</td>
              <td className="px-4 py-3 whitespace-nowrap text-sm">{d.razao_social}</td>
              <td className="px-4 py-3 whitespace-nowrap text-sm">{d.uf}</td>
              <td className="px-4 py-3 whitespace-nowrap text-sm">{d.cidade}</td>
              <td className="px-4 py-3 whitespace-nowrap text-sm text-right space-x-2">
                <button
                  onClick={() => onEdit(d)}
                  className="text-indigo-600 hover:text-indigo-900"
                  aria-label="Editar"
                >
                  Editar
                </button>
                <button
                  onClick={() => onDelete(d.id)}
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
