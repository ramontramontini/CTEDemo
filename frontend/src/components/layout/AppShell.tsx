import { ReactNode, useState } from 'react';
import { Link } from 'react-router-dom';
import { useResetData } from '@/api/hooks/useResetData';

interface AppShellProps {
  children: ReactNode;
}

export function AppShell({ children }: AppShellProps) {
  const resetMutation = useResetData();
  const [showFeedback, setShowFeedback] = useState(false);

  const handleReset = () => {
    resetMutation.mutate(undefined, {
      onSuccess: () => {
        setShowFeedback(true);
        setTimeout(() => setShowFeedback(false), 2000);
      },
    });
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <nav className="bg-gray-800">
        <div className="max-w-7xl mx-auto px-4">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center">
              <span className="text-white font-bold text-lg">CTEDemo</span>
              <div className="ml-10 flex items-baseline space-x-4">

          <Link to="/cte" className="text-gray-300 hover:text-white px-3 py-2 rounded-md text-sm font-medium">Cte</Link>
          <Link to="/remetente" className="text-gray-300 hover:text-white px-3 py-2 rounded-md text-sm font-medium">Remetente</Link>
          <Link to="/destinatario" className="text-gray-300 hover:text-white px-3 py-2 rounded-md text-sm font-medium">Destinatario</Link>
          <Link to="/transportadora" className="text-gray-300 hover:text-white px-3 py-2 rounded-md text-sm font-medium">Transportadora</Link>
              </div>
            </div>
            <div className="flex items-center gap-2">
              {showFeedback && (
                <span className="text-green-400 text-sm">Dados resetados</span>
              )}
              <button
                type="button"
                onClick={handleReset}
                disabled={resetMutation.isPending}
                className="bg-orange-600 hover:bg-orange-700 disabled:opacity-50 text-white px-3 py-1.5 rounded text-sm font-medium"
              >
                {resetMutation.isPending ? 'Resetando...' : 'Limpar Dados'}
              </button>
            </div>
          </div>
        </div>
      </nav>
      <main className="max-w-7xl mx-auto px-4 py-6">
        {children}
      </main>
    </div>
  );
}
