import { Routes, Route, Navigate } from 'react-router-dom';
import { AppShell } from './components/layout/AppShell';

import { CtePage } from './pages/Cte/CtePage';
import { RemetentePage } from './pages/Remetente/RemetentePage';
import { DestinatarioPage } from './pages/Destinatario/DestinatarioPage';
import { TransportadoraPage } from './pages/Transportadora/TransportadoraPage';

function App() {
  return (
    <AppShell>
      <Routes>

          <Route path="/cte" element={<CtePage />} />
          <Route path="/remetente" element={<RemetentePage />} />
          <Route path="/destinatario" element={<DestinatarioPage />} />
          <Route path="/transportadora" element={<TransportadoraPage />} />
        <Route path="*" element={<Navigate to="/cte" replace />} />
      </Routes>
    </AppShell>
  );
}

export default App;
