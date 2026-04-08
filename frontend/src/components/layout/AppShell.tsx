import { ReactNode } from 'react';
import { Link } from 'react-router-dom';

interface AppShellProps {
  children: ReactNode;
}

export function AppShell({ children }: AppShellProps) {
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
          </div>
        </div>
      </nav>
      <main className="max-w-7xl mx-auto px-4 py-6">
        {children}
      </main>
    </div>
  );
}
