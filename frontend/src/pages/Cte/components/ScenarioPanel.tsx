import { useState } from 'react';
import type { Scenario } from '../scenarios';
import { SCENARIO_CATEGORIES } from '../scenarios';
import type { ScenarioResult } from '../hooks/useScenarioRunner';
import { ScenarioReportModal } from './ScenarioReportModal';

interface ScenarioPanelProps {
  scenarios: Scenario[];
  onSelect: (scenario: Scenario) => void;
  selectedId: string | null;
  onRunOne?: (scenarioId: string) => void;
  onRunAll?: () => void;
  results?: Record<string, ScenarioResult>;
  runningId?: string | null;
  isRunningAll?: boolean;
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

export function ScenarioPanel({
  scenarios,
  onSelect,
  selectedId,
  onRunOne,
  onRunAll,
  results = {},
  runningId = null,
  isRunningAll = false,
}: ScenarioPanelProps) {
  const [showReport, setShowReport] = useState(false);

  const grouped = CATEGORY_ORDER.map((cat) => ({
    category: cat,
    config: SCENARIO_CATEGORIES[cat],
    items: scenarios.filter((s) => s.category === cat),
  })).filter((g) => g.items.length > 0);

  const resultEntries = Object.values(results);
  const passedCount = resultEntries.filter(r => r.passed).length;
  const totalCount = resultEntries.length;

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-xl font-semibold text-gray-900">Cenarios de Teste</h2>
        <div className="flex items-center gap-4">
          {totalCount > 0 && (
            <>
              <span className={`text-sm font-medium ${passedCount === totalCount ? 'text-green-600' : 'text-orange-600'}`}>
                {passedCount}/{totalCount} passaram
              </span>
              <button
                type="button"
                onClick={() => setShowReport(true)}
                className="bg-green-600 hover:bg-green-700 text-white px-3 py-1.5 rounded text-sm font-medium"
              >
                Ver Relatorio
              </button>
            </>
          )}
          {onRunAll && (
            <button
              type="button"
              onClick={onRunAll}
              disabled={isRunningAll}
              className="bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white px-3 py-1.5 rounded text-sm font-medium"
            >
              {isRunningAll ? 'Executando...' : 'Executar Todos'}
            </button>
          )}
        </div>
      </div>
      <div className="space-y-6">
        {grouped.map((group) => (
          <div key={group.category}>
            <h3 className="text-sm font-medium text-gray-500 uppercase tracking-wider mb-3">
              {group.config.label} ({group.items.length})
            </h3>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
              {group.items.map((scenario) => (
                <ScenarioCard
                  key={scenario.id}
                  scenario={scenario}
                  isSelected={selectedId === scenario.id}
                  onSelect={() => onSelect(scenario)}
                  onRun={onRunOne ? () => onRunOne(scenario.id) : undefined}
                  result={results[scenario.id]}
                  isRunning={runningId === scenario.id}
                />
              ))}
            </div>
          </div>
        ))}
      </div>

      {showReport && (
        <ScenarioReportModal
          scenarios={scenarios}
          results={results}
          onClose={() => setShowReport(false)}
        />
      )}
    </div>
  );
}

interface ScenarioCardProps {
  scenario: Scenario;
  isSelected: boolean;
  onSelect: () => void;
  onRun?: () => void;
  result?: ScenarioResult;
  isRunning: boolean;
}

function ScenarioCard({ scenario, isSelected, onSelect, onRun, result, isRunning }: ScenarioCardProps) {
  const [expanded, setExpanded] = useState(false);

  return (
    <div
      className={`text-left p-3 rounded-lg border transition-all ${
        isSelected
          ? 'ring-2 ring-blue-500 border-blue-300 bg-blue-50'
          : 'border-gray-200 hover:border-gray-300'
      }`}
    >
      <button
        type="button"
        onClick={onSelect}
        className="w-full text-left"
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

      <div className="mt-2 pt-2 border-t border-gray-100">
        <div className="flex items-center gap-2">
          {onRun && (
            <button
              type="button"
              onClick={(e) => { e.stopPropagation(); onRun(); }}
              disabled={isRunning}
              className="bg-gray-100 hover:bg-gray-200 disabled:opacity-50 text-gray-700 px-2 py-1 rounded text-xs font-medium"
            >
              Executar
            </button>
          )}

          {isRunning && (
            <span data-testid={`spinner-${scenario.id}`} className="text-xs text-blue-500 animate-pulse">
              Executando...
            </span>
          )}

          {result && !isRunning && (
            <div data-testid={`result-${scenario.id}`} className="flex items-center gap-1.5">
              <span className={`text-sm ${result.passed ? 'text-green-600' : 'text-red-600'}`}>
                {result.passed ? '\u2713' : '\u2717'}
              </span>
              <span className={`text-xs font-medium ${result.passed ? 'text-green-700' : 'text-red-700'}`}>
                {result.statusCode}
              </span>
            </div>
          )}
        </div>

        {result && !isRunning && (
          <div className="mt-1">
            <button
              type="button"
              onClick={() => setExpanded(!expanded)}
              className="text-xs text-gray-400 hover:text-gray-600"
            >
              {expanded ? '\u25BC Resposta JSON' : '\u25B6 Resposta JSON'}
            </button>
            {expanded && (
              <pre className="mt-1 p-2 bg-gray-50 rounded text-xs text-gray-600 overflow-auto max-h-40">
                {JSON.stringify(result.body, null, 2)}
              </pre>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
