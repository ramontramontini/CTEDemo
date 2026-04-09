import { describe, it, expect } from 'vitest';
import { SCENARIOS, SCENARIO_CATEGORIES } from '@/pages/Cte/scenarios';
import type { Scenario } from '@/pages/Cte/scenarios';

const SEEDED_TRANSPORTADORA_CNPJS = ['16003754000135', '33014556000196'];
const SEEDED_NFE_KEYS = {
  authorized: [
    '35251003026527000183550010013119001683587366',
    '35251003026527000183550010013119001683587367',
    '35251003026527000183550010013119001683587368',
    '35251003026527000183550010013119001683587369',
    '31230499888777000166550010000000031000000039',
    '35230410758386000159550010000000011000000015',
  ],
  canceled: ['35230410758386000159550010000000021000000022'],
};
const VALID_CATEGORIES = ['success', 'business_error', 'validation_error', 'cfop_error'] as const;

describe('SCENARIOS', () => {
  it('has at least 19 scenario entries', () => {
    expect(SCENARIOS.length).toBeGreaterThanOrEqual(19);
  });

  it('all IDs are unique', () => {
    const ids = SCENARIOS.map((s: Scenario) => s.id);
    expect(new Set(ids).size).toBe(ids.length);
  });

  it('all FreightOrder values are unique except the duplicate scenario', () => {
    const duplicateScenario = SCENARIOS.find((s: Scenario) => s.id === 'duplicate-freight-order');
    const others = SCENARIOS.filter((s: Scenario) => s.id !== 'duplicate-freight-order');
    const freightOrders = others.map((s: Scenario) => s.payload.FreightOrder).filter(Boolean);
    expect(new Set(freightOrders).size).toBe(freightOrders.length);
    // Duplicate scenario intentionally reuses happy path FreightOrder
    if (duplicateScenario) {
      const happyPath = SCENARIOS.find((s: Scenario) => s.id === 'happy-path');
      expect(duplicateScenario.payload.FreightOrder).toBe(happyPath?.payload.FreightOrder);
    }
  });

  it('each scenario has all required fields with correct types', () => {
    for (const s of SCENARIOS) {
      expect(typeof s.id).toBe('string');
      expect(typeof s.name).toBe('string');
      expect(typeof s.description).toBe('string');
      expect(VALID_CATEGORIES).toContain(s.category);
      expect([201, 400, 422]).toContain(s.expectedStatus);
      expect(typeof s.expectedOutcome).toBe('string');
      expect(typeof s.payload).toBe('object');
    }
  });

  it('covers all 4 categories', () => {
    const categories = new Set(SCENARIOS.map((s: Scenario) => s.category));
    for (const cat of VALID_CATEGORIES) {
      expect(categories.has(cat)).toBe(true);
    }
  });

  it('success scenarios use registered Carrier CNPJs from seed data', () => {
    const successScenarios = SCENARIOS.filter((s: Scenario) => s.category === 'success');
    for (const s of successScenarios) {
      expect(SEEDED_TRANSPORTADORA_CNPJS).toContain(s.payload.Carrier);
    }
  });

  it('canceled NF-e scenario uses the known canceled key', () => {
    const scenario = SCENARIOS.find((s: Scenario) => s.id === 'nfe-canceled');
    expect(scenario).toBeDefined();
    const nfeKeys = scenario!.payload.Folder?.[0]?.RelatedNFE ?? [];
    const hasCanceled = nfeKeys.some((k: string) => SEEDED_NFE_KEYS.canceled.includes(k));
    expect(hasCanceled).toBe(true);
  });
});

describe('SCENARIO_CATEGORIES', () => {
  it('has entries for all 4 categories', () => {
    for (const cat of VALID_CATEGORIES) {
      expect(SCENARIO_CATEGORIES[cat]).toBeDefined();
      expect(typeof SCENARIO_CATEGORIES[cat].label).toBe('string');
      expect(typeof SCENARIO_CATEGORIES[cat].color).toBe('string');
    }
  });
});
