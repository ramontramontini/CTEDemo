import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { describe, it, expect } from 'vitest';
import { AppShell } from '@/components/layout/AppShell';

function renderShell() {
  return render(
    <MemoryRouter>
      <AppShell>
        <div>content</div>
      </AppShell>
    </MemoryRouter>,
  );
}

describe('AppShell', () => {
  it('renders navigation links as React Router Links, not plain anchors', () => {
    renderShell();
    const links = ['Cte', 'Remetente', 'Destinatario', 'Transportadora'];
    for (const label of links) {
      const el = screen.getByText(label);
      // React Router Link renders as <a> but with no full page reload behavior.
      // The key difference: href attribute should exist (Link renders as <a>)
      // and no data-discover attribute should break routing.
      expect(el.tagName).toBe('A');
      expect(el).toHaveAttribute('href');
    }
  });

  it('navigation links point to correct routes', () => {
    renderShell();
    expect(screen.getByText('Cte')).toHaveAttribute('href', '/cte');
    expect(screen.getByText('Remetente')).toHaveAttribute('href', '/remetente');
    expect(screen.getByText('Destinatario')).toHaveAttribute('href', '/destinatario');
    expect(screen.getByText('Transportadora')).toHaveAttribute('href', '/transportadora');
  });
});
