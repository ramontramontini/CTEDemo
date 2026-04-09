import type { Scenario } from '../scenarios';
import { SCENARIO_CATEGORIES } from '../scenarios';

interface ScenarioPanelProps {
  scenarios: Scenario[];
  onSelect: (scenario: Scenario) => void;
  selectedId: string | null;
}

const STATUS_BADGE_COLORS: Record<number, string> = {
  201: 'bg-green-100 text-green-800',
  400: 'bg-orange-100 text-orange-800',
  422: 'bg-red-100 text-red-800',
};

const CATEGORY_ORDER: Scenario['category'][] = [
  'success',
  'business_error',
  'validation_error',
  'cfop_error',
];

export function ScenarioPanel({ scenarios, onSelect, selectedId }: ScenarioPanelProps) {
  const grouped = CATEGORY_ORDER.map((cat) => ({
    category: cat,
    config: SCENARIO_CATEGORIES[cat],
    items: scenarios.filter((s) => s.category === cat),
  })).filter((g) => g.items.length > 0);

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h2 className="text-xl font-semibold text-gray-900 mb-4">Cenarios de Teste</h2>
      <div className="space-y-6">
        {grouped.map((group) => (
          <div key={group.category}>
            <h3 className="text-sm font-medium text-gray-500 uppercase tracking-wider mb-3">
              {group.config.label} ({group.items.length})
            </h3>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
              {group.items.map((scenario) => (
                <button
                  key={scenario.id}
                  type="button"
                  onClick={() => onSelect(scenario)}
                  className={`text-left p-3 rounded-lg border transition-all hover:shadow-md ${
                    selectedId === scenario.id
                      ? 'ring-2 ring-blue-500 border-blue-300 bg-blue-50'
                      : 'border-gray-200 hover:border-gray-300'
                  }`}
                >
                  <div className="flex items-center gap-2 mb-1">
                    <span
                      className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${
                        STATUS_BADGE_COLORS[scenario.expectedStatus] ?? 'bg-gray-100 text-gray-800'
                      }`}
                    >
                      {scenario.expectedStatus}
                    </span>
                    <span className="text-sm font-medium text-gray-900">
                      {scenario.name}
                    </span>
                  </div>
                  <p className="text-xs text-gray-500">{scenario.description}</p>
                </button>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
