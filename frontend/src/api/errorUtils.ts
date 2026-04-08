import axios from 'axios';

export function extractErrorMessage(error: unknown): string {
  if (axios.isAxiosError(error)) {
    if (!error.response) {
      return 'Erro de conexao — nao foi possivel conectar ao servidor';
    }
    const { status, statusText, data } = error.response;
    const detail = data?.detail;
    if (typeof detail === 'string' && detail.length > 0) {
      return `${status} — ${detail}`;
    }
    return `${status} — ${statusText}`;
  }
  if (error instanceof Error) {
    return error.message;
  }
  return 'Erro desconhecido';
}
