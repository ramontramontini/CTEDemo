import { useEffect, useState } from 'react';
import type { Scenario } from '../scenarios';
import { SCENARIO_CATEGORIES } from '../scenarios';
import type { ScenarioResult } from '../hooks/useScenarioRunner';

const CATEGORY_ORDER: Scenario['category'][] = [
  'success',
  'business_error',
  'validation_error',
  'cfop_error',
];

const STATUS_BADGE_COLORS: Record<number, string> = {
  201: 'bg-green-100 text-green-800',
  400: 'bg-orange-100 text-orange-800',
  422: 'bg-red-100 text-red-800',
};

interface ScenarioReportModalProps {
  scenarios: Scenario[];
  results: Record<string, ScenarioResult>;
  onClose: () => void;
}

export function ScenarioReportModal({ scenarios, results, onClose }: ScenarioReportModalProps) {
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [onClose]);

  const grouped = CATEGORY_ORDER.map((cat) => ({
    category: cat,
    config: SCENARIO_CATEGORIES[cat],
    items: scenarios.filter((s) => s.category === cat),
  })).filter((g) => g.items.length > 0);

  const resultEntries = Object.values(results);
  const passedCount = resultEntries.filter((r) => r.passed).length;
  const totalCount = resultEntries.length;

  return (
    <div
      data-testid="report-modal"
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/50"
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
    >
      <div className="bg-white rounded-lg shadow-xl w-full max-w-5xl mx-4 max-h-[90vh] flex flex-col">
        <div className="flex items-center justify-between p-6 border-b">
          <div>
            <h2 className="text-xl font-semibold text-gray-900">Relatorio de Cenarios</h2>
            {totalCount > 0 && (
              <span className={`text-sm font-medium ${passedCount === totalCount ? 'text-green-600' : 'text-orange-600'}`}>
                {passedCount}/{totalCount} passaram
              </span>
            )}
          </div>
          <button
            type="button"
            onClick={onClose}
            aria-label="Fechar"
            className="text-gray-400 hover:text-gray-600 text-2xl leading-none"
          >
            &times;
          </button>
        </div>

        <div className="p-6 overflow-y-auto">
          <div className="space-y-6">
            {grouped.map((group) => (
              <div key={group.category}>
                <h3 className="text-sm font-medium text-gray-500 uppercase tracking-wider mb-3">
                  {group.config.label} ({group.items.length})
                </h3>
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
                  {group.items.map((scenario) => {
                    const result = results[scenario.id];
                    const jsonText = result
                      ? JSON.stringify(result.body, null, 2)
                      : '{}';

                    return (
                      <div key={scenario.id} className="p-3 rounded-lg border border-gray-200">
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

                        {result && (
                          <div className="flex items-center gap-1.5 mb-2">
                            <span className={`text-sm ${result.passed ? 'text-green-600' : 'text-red-600'}`}>
                              {result.passed ? '\u2713' : '\u2717'}
                            </span>
                            <span className={`text-xs font-medium ${result.passed ? 'text-green-700' : 'text-red-700'}`}>
                              {result.statusCode}
                            </span>
                          </div>
                        )}

                        <CopyJsonButton jsonText={jsonText} />

                        <pre className="p-2 bg-gray-50 rounded text-xs text-gray-600 overflow-auto max-h-60">
                          {jsonText}
                        </pre>
                      </div>
                    );
                  })}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

function CopyJsonButton({ jsonText }: { jsonText: string }) {
  const [feedback, setFeedback] = useState<string | null>(null);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(jsonText);
      setFeedback('Copiado!');
    } catch {
      setFeedback('Erro ao copiar');
    }
    setTimeout(() => setFeedback(null), 1500);
  };

  return (
    <div className="flex items-center gap-2 mb-2">
      <button
        type="button"
        onClick={handleCopy}
        className="bg-gray-100 hover:bg-gray-200 text-gray-700 px-2 py-1 rounded text-xs font-medium"
      >
        Copiar JSON
      </button>
      {feedback && (
        <span className={`text-xs font-medium ${feedback === 'Copiado!' ? 'text-green-600' : 'text-red-600'}`}>
          {feedback}
        </span>
      )}
    </div>
  );
}
