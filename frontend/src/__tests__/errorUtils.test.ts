import { describe, it, expect } from 'vitest';
import { extractErrorMessage } from '@/api/errorUtils';
import { AxiosError, AxiosHeaders } from 'axios';

function makeAxiosError(status: number, detail: string | undefined, statusText = 'Error'): AxiosError {
  const headers = new AxiosHeaders();
  const error = new AxiosError(
    `Request failed with status code ${status}`,
    'ERR_BAD_REQUEST',
    undefined,
    undefined,
    {
      status,
      statusText,
      data: detail !== undefined ? { detail } : {},
      headers,
      config: { headers },
    },
  );
  return error;
}

describe('extractErrorMessage', () => {
  it('extracts status and detail from AxiosError with response', () => {
    const err = makeAxiosError(400, 'Transportadora not found for CNPJ 10758386000159');
    expect(extractErrorMessage(err)).toBe('400 — Transportadora not found for CNPJ 10758386000159');
  });

  it('falls back to statusText when detail is missing', () => {
    const err = makeAxiosError(404, undefined, 'Not Found');
    expect(extractErrorMessage(err)).toBe('404 — Not Found');
  });

  it('handles network errors without response', () => {
    const err = new AxiosError('Network Error', 'ERR_NETWORK');
    const msg = extractErrorMessage(err);
    expect(msg).toContain('conexao');
  });

  it('handles generic non-Axios errors', () => {
    const err = new Error('Something broke');
    expect(extractErrorMessage(err)).toBe('Something broke');
  });

  it('handles unknown error types', () => {
    expect(extractErrorMessage('string error')).toBe('Erro desconhecido');
  });

  it('handles detail as object (array of validation errors)', () => {
    const headers = new AxiosHeaders();
    const err = new AxiosError(
      'Request failed',
      'ERR_BAD_REQUEST',
      undefined,
      undefined,
      {
        status: 422,
        statusText: 'Unprocessable Entity',
        data: { detail: [{ field: 'Weight', message: 'Weight must be positive' }] },
        headers,
        config: { headers },
      },
    );
    const msg = extractErrorMessage(err);
    expect(msg).toBe('422 — Unprocessable Entity');
  });
});
