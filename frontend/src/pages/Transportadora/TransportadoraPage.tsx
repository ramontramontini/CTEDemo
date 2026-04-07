import { useTransportadoras } from '@/api/hooks/useTransportadoras';

export function TransportadoraPage() {
  const { data: items, isLoading, error } = useTransportadoras();

  if (isLoading) return <div className="text-gray-500">Loading...</div>;
  if (error) return <div className="text-red-500">Error loading transportadoras</div>;

  return (
    <div>
      <h1 className="text-2xl font-bold text-gray-900 mb-4">Transportadoras</h1>
      {items && items.length > 0 ? (
        <ul className="space-y-2">
          {items.map((item) => (
            <li key={item.id} className="bg-white p-4 rounded-lg shadow">
              <span className="font-medium">{item.name}</span>
              <span className="ml-2 text-sm text-gray-500">{item.status}</span>
            </li>
          ))}
        </ul>
      ) : (
        <p className="text-gray-500">No transportadoras yet.</p>
      )}
    </div>
  );
}
