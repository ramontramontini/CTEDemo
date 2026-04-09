import axios from 'axios';
import type { Cte, Remetente, CreateRemetenteRequest, UpdateRemetenteRequest, Destinatario, CreateDestinatarioRequest, UpdateDestinatarioRequest, Transportadora, CreateTransportadoraRequest, UpdateTransportadoraRequest, ValidationError } from '../types';

const client = axios.create({
  baseURL: (import.meta.env.VITE_API_BASE_URL || '') + '/api/v1',
});

export const api = {

  // Cte endpoints
  listCtes: () => client.get<Cte[]>('/cte').then(r => r.data),
  getCte: (id: string) => client.get<Cte>(`/cte/${id}`).then(r => r.data),
  generateCte: async (data: Record<string, unknown>): Promise<Cte> => {
    try {
      const response = await client.post<Cte>('/cte', data);
      return response.data;
    } catch (error) {
      if (axios.isAxiosError(error) && error.response?.status === 422) {
        const detail = error.response.data?.detail as ValidationError[] | undefined;
        const validationError = new Error('Validation failed');
        (validationError as unknown as Record<string, unknown>).validationErrors = detail || [];
        throw validationError;
      }
      throw error;
    }
  },

  // Remetente endpoints
  listRemetentes: () => client.get<Remetente[]>('/remetentes').then(r => r.data),
  getRemetente: (id: string) => client.get<Remetente>(`/remetentes/${id}`).then(r => r.data),
  createRemetente: (data: CreateRemetenteRequest) => client.post<Remetente>('/remetentes', data).then(r => r.data),
  updateRemetente: (id: string, data: UpdateRemetenteRequest) => client.patch<Remetente>(`/remetentes/${id}`, data).then(r => r.data),
  deleteRemetente: (id: string) => client.delete(`/remetentes/${id}`),

  // Destinatario endpoints
  listDestinatarios: () => client.get<Destinatario[]>('/destinatarios').then(r => r.data),
  getDestinatario: (id: string) => client.get<Destinatario>(`/destinatarios/${id}`).then(r => r.data),
  createDestinatario: (data: CreateDestinatarioRequest) => client.post<Destinatario>('/destinatarios', data).then(r => r.data),
  updateDestinatario: (id: string, data: UpdateDestinatarioRequest) => client.patch<Destinatario>(`/destinatarios/${id}`, data).then(r => r.data),
  deleteDestinatario: (id: string) => client.delete(`/destinatarios/${id}`),

  // Dev endpoints
  resetData: () => client.post('/dev/reset-data').then(r => r.data),

  // Transportadora endpoints
  listTransportadoras: () => client.get<Transportadora[]>('/transportadoras').then(r => r.data),
  getTransportadora: (id: string) => client.get<Transportadora>(`/transportadoras/${id}`).then(r => r.data),
  createTransportadora: (data: CreateTransportadoraRequest) => client.post<Transportadora>('/transportadoras', data).then(r => r.data),
  updateTransportadora: (id: string, data: UpdateTransportadoraRequest) => client.patch<Transportadora>(`/transportadoras/${id}`, data).then(r => r.data),
  deleteTransportadora: (id: string) => client.delete(`/transportadoras/${id}`).then(r => r.data),
};
