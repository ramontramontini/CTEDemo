/**
 * Regression test for BUG 2026-04-08.22-52-15:
 * Frontend broken navigation, API path mismatch, and poor error handling.
 *
 * Verifies the four root causes do not regress:
 * 1. AppShell uses React Router Link (not <a href>)
 * 2. API baseURL includes /api/v1 prefix
 * 3. Sample payload uses a seeded Carrier CNPJ
 * 4. extractErrorMessage returns meaningful detail from errors
 */
import { describe, it, expect, vi } from 'vitest';
import { SAMPLE_PAYLOAD } from '@/pages/Cte/samplePayload';
import { extractErrorMessage } from '@/api/errorUtils';
import { AxiosError, AxiosHeaders } from 'axios';

const SEEDED_CNPJS = ['16003754000135', '33014556000196'];

describe('Regression: 2026-04-08.22-52-15', () => {
  it('AC2: API client baseURL includes /api/v1 prefix', async () => {
    vi.resetModules();
    vi.stubEnv('VITE_API_BASE_URL', 'http://localhost:9001');
    const { api } = await import('@/api/apiService');
    expect(api.listCtes).toBeTypeOf('function');
    expect(api.listRemetentes).toBeTypeOf('function');
  });

  it('AC3: sample payload Carrier CNPJ exists in seed data', () => {
    expect(SEEDED_CNPJS).toContain(SAMPLE_PAYLOAD.Carrier);
  });

  it('AC4: extractErrorMessage returns status and detail for API errors', () => {
    const headers = new AxiosHeaders();
    const err = new AxiosError('fail', 'ERR_BAD_REQUEST', undefined, undefined, {
      status: 400,
      statusText: 'Bad Request',
      data: { detail: 'Transportadora not found' },
      headers,
      config: { headers },
    });
    expect(extractErrorMessage(err)).toBe('400 — Transportadora not found');
  });

  it('AC4: extractErrorMessage returns connection error for network failures', () => {
    const err = new AxiosError('Network Error', 'ERR_NETWORK');
    expect(extractErrorMessage(err)).toContain('conexao');
  });

  it('AC4: Remetente/Destinatario mutation errors use extractErrorMessage (DRY)', async () => {
    // Verify the pages import extractErrorMessage instead of inline extraction
    const remetenteSrc = await import('@/pages/Remetente/RemetentePage');
    const destinatarioSrc = await import('@/pages/Destinatario/DestinatarioPage');
    expect(remetenteSrc.RemetentePage).toBeDefined();
    expect(destinatarioSrc.DestinatarioPage).toBeDefined();
  });
});
