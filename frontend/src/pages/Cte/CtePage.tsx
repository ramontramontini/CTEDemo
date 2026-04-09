import { useState } from 'react';
import { useCtes, useGenerateCte } from '@/api/hooks/useCtes';
import { extractErrorMessage } from '@/api/errorUtils';
import type { Cte, ValidationError } from '@/types';
import type { Scenario } from './scenarios';
import { SCENARIOS } from './scenarios';
import { CteForm } from './components/CteForm';
import { CteResult } from './components/CteResult';
import { CteList } from './components/CteList';
import { ValidationErrors } from './components/ValidationErrors';
import { ScenarioPanel } from './components/ScenarioPanel';
import { useScenarioRunner } from './hooks/useScenarioRunner';

export function CtePage() {
  const { data: ctes, isLoading: listLoading, error: listError } = useCtes();
  const generateMutation = useGenerateCte();
  const [lastResult, setLastResult] = useState<Cte | null>(null);
  const [validationErrors, setValidationErrors] = useState<ValidationError[] | null>(null);
  const [generateError, setGenerateError] = useState<string | null>(null);
  const [selectedScenario, setSelectedScenario] = useState<Scenario | null>(null);
  const [externalJson, setExternalJson] = useState<string | null>(null);

  const { results, runningId, isRunningAll, runOne, runAll } = useScenarioRunner(SCENARIOS);

  const handleSubmit = (payload: Record<string, unknown>) => {
    setValidationErrors(null);
    setLastResult(null);
    setGenerateError(null);
    generateMutation.mutate(payload, {
      onSuccess: (data) => {
        setLastResult(data);
        setValidationErrors(null);
      },
      onError: (error) => {
        const errs = (error as unknown as Record<string, unknown>).validationErrors as ValidationError[] | undefined;
        if (errs) {
          setValidationErrors(errs);
        } else {
          setGenerateError(extractErrorMessage(error));
        }
      },
    });
  };

  const handleScenarioSelect = (scenario: Scenario) => {
    setSelectedScenario(scenario);
    setExternalJson(JSON.stringify(scenario.payload, null, 2));
    setValidationErrors(null);
    setLastResult(null);
    setGenerateError(null);
  };

  return (
    <div className="space-y-6">
      <CteForm
        onSubmit={handleSubmit}
        isLoading={generateMutation.isPending}
        errors={validationErrors}
        externalJson={externalJson}
        expectedOutcome={selectedScenario?.expectedOutcome ?? null}
      />

      {validationErrors && <ValidationErrors errors={validationErrors} />}

      {generateError && (
        <p className="text-red-500 text-sm">{generateError}</p>
      )}

      {lastResult && <CteResult cte={lastResult} />}

      <ScenarioPanel
        scenarios={SCENARIOS}
        onSelect={handleScenarioSelect}
        selectedId={selectedScenario?.id ?? null}
        onRunOne={runOne}
        onRunAll={runAll}
        results={results}
        runningId={runningId}
        isRunningAll={isRunningAll}
      />

      <div>
        <h2 className="text-xl font-semibold text-gray-900 mb-4">CT-es Gerados</h2>
        {listLoading ? (
          <p className="text-gray-500">Carregando...</p>
        ) : listError ? (
          <p className="text-red-500 text-sm">Erro ao carregar CT-es: {extractErrorMessage(listError)}</p>
        ) : (
          <CteList ctes={ctes || []} />
        )}
      </div>
    </div>
  );
}
