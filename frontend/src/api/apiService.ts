import axios from 'axios';
import type { Cte, CreateCteRequest, Remetente, CreateRemetenteRequest, Destinatario, CreateDestinatarioRequest, Transportadora, CreateTransportadoraRequest } from '../types';

const client = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api/v1',
});

export const api = {


  // Cte endpoints
  listCtes: () => client.get<Cte[]>('/ctes').then(r => r.data),
  getCte: (id: string) => client.get<Cte>(`/ctes/${id}`).then(r => r.data),
  createCte: (data: CreateCteRequest) => client.post<Cte>('/ctes', data).then(r => r.data),

  // Remetente endpoints
  listRemetentes: () => client.get<Remetente[]>('/remetentes').then(r => r.data),
  getRemetente: (id: string) => client.get<Remetente>(`/remetentes/${id}`).then(r => r.data),
  createRemetente: (data: CreateRemetenteRequest) => client.post<Remetente>('/remetentes', data).then(r => r.data),

  // Destinatario endpoints
  listDestinatarios: () => client.get<Destinatario[]>('/destinatarios').then(r => r.data),
  getDestinatario: (id: string) => client.get<Destinatario>(`/destinatarios/${id}`).then(r => r.data),
  createDestinatario: (data: CreateDestinatarioRequest) => client.post<Destinatario>('/destinatarios', data).then(r => r.data),

  // Transportadora endpoints
  listTransportadoras: () => client.get<Transportadora[]>('/transportadoras').then(r => r.data),
  getTransportadora: (id: string) => client.get<Transportadora>(`/transportadoras/${id}`).then(r => r.data),
  createTransportadora: (data: CreateTransportadoraRequest) => client.post<Transportadora>('/transportadoras', data).then(r => r.data),
};
