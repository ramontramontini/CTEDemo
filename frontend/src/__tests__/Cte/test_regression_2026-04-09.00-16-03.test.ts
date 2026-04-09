import { describe, it, expect } from 'vitest';
import { SAMPLE_PAYLOAD } from '@/pages/Cte/samplePayload';

const SEEDED_REMETENTE_CNPJS = ['03026527000183', '11444777000161'];
const SEEDED_NFE_KEYS_AUTHORIZED = [
  '35251003026527000183550010013119001683587366',
  '35251003026527000183550010013119001683587367',
  '35251003026527000183550010013119001683587368',
  '35251003026527000183550010013119001683587369',
  '31230499888777000166550010000000031000000039',
  '35230410758386000159550010000000011000000015',
];

describe('Regression 2026-04-09.00-16-03: sample payload seed data mismatch', () => {
  it('CNPJ_Origin is a seeded Remetente CNPJ', () => {
    expect(SEEDED_REMETENTE_CNPJS).toContain(SAMPLE_PAYLOAD.CNPJ_Origin);
  });

  it('RelatedNFE uses seeded authorized NFE keys', () => {
    const folder = SAMPLE_PAYLOAD.Folder[0];
    expect(folder.RelatedNFE.length).toBeGreaterThan(0);
    for (const nfeKey of folder.RelatedNFE) {
      expect(SEEDED_NFE_KEYS_AUTHORIZED).toContain(nfeKey);
    }
  });

  it('CNPJ_Origin matches emitter CNPJ in referenced NFE keys', () => {
    const folder = SAMPLE_PAYLOAD.Folder[0];
    for (const nfeKey of folder.RelatedNFE) {
      const emitterCnpj = nfeKey.substring(6, 20);
      expect(emitterCnpj).toBe(SAMPLE_PAYLOAD.CNPJ_Origin);
    }
  });
});
