import { useState, useCallback } from 'react';
import { api } from '@/api/apiService';
import type { Scenario } from '../scenarios';

export interface ScenarioResult {
  statusCode: number;
  body: Record<string, unknown>;
  passed: boolean;
}

export function useScenarioRunner(scenarios: Scenario[]) {
  const [results, setResults] = useState<Record<string, ScenarioResult>>({});
  const [runningId, setRunningId] = useState<string | null>(null);
  const [isRunningAll, setIsRunningAll] = useState(false);

  const executeScenario = useCallback(async (scenario: Scenario): Promise<ScenarioResult> => {
    try {
      const data = await api.generateCte(scenario.payload);
      return {
        statusCode: 201,
        body: data as unknown as Record<string, unknown>,
        passed: scenario.expectedStatus === 201,
      };
    } catch (error: unknown) {
      const axiosError = error as { response?: { status: number; data: unknown }; validationErrors?: unknown[] };
      if (axiosError.validationErrors) {
        return {
          statusCode: 422,
          body: { detail: axiosError.validationErrors },
          passed: scenario.expectedStatus === 422,
        };
      }
      const status = axiosError.response?.status ?? 0;
      const body = (axiosError.response?.data ?? { detail: 'Erro de rede' }) as Record<string, unknown>;
      return {
        statusCode: status,
        body,
        passed: scenario.expectedStatus === status,
      };
    }
  }, []);

  const runOne = useCallback(async (scenarioId: string) => {
    const scenario = scenarios.find(s => s.id === scenarioId);
    if (!scenario) return;

    setRunningId(scenarioId);
    const result = await executeScenario(scenario);
    setResults(prev => ({ ...prev, [scenarioId]: result }));
    setRunningId(null);
  }, [scenarios, executeScenario]);

  const runAll = useCallback(async () => {
    setIsRunningAll(true);
    setResults({});

    for (const scenario of scenarios) {
      setRunningId(scenario.id);
      const result = await executeScenario(scenario);
      setResults(prev => ({ ...prev, [scenario.id]: result }));
    }

    setRunningId(null);
    setIsRunningAll(false);
  }, [scenarios, executeScenario]);

  return { results, runningId, isRunningAll, runOne, runAll };
}
