import { useCtes } from '@/api/hooks/useCtes';

export function CtePage() {
  const { data: items, isLoading, error } = useCtes();

  if (isLoading) return <div className="text-gray-500">Loading...</div>;
  if (error) return <div className="text-red-500">Error loading ctes</div>;

  return (
    <div>
      <h1 className="text-2xl font-bold text-gray-900 mb-4">Ctes</h1>
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
        <p className="text-gray-500">No ctes yet.</p>
      )}
    </div>
  );
}
