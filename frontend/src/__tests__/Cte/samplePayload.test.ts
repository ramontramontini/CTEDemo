import { describe, it, expect } from 'vitest';
import { SAMPLE_PAYLOAD } from '@/pages/Cte/samplePayload';

const SEEDED_TRANSPORTADORA_CNPJS = ['16003754000135', '33014556000196'];

describe('SAMPLE_PAYLOAD', () => {
  it('uses a Carrier CNPJ that exists in seed data', () => {
    expect(SEEDED_TRANSPORTADORA_CNPJS).toContain(SAMPLE_PAYLOAD.Carrier);
  });

  it('has a valid 14-digit FreightOrder', () => {
    expect(SAMPLE_PAYLOAD.FreightOrder).toMatch(/^\d{14}$/);
  });
});
