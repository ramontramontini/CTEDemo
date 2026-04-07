/**
 * TypeScript interfaces mirroring backend DTOs.
 */

export interface Cte {
  id: string;
  name: string;
  status: string;
  created_at: string;
  updated_at: string | null;
}

export interface CreateCteRequest {
  name: string;
}

export interface UpdateCteRequest {
  name?: string;
}

export interface Remetente {
  id: string;
  name: string;
  status: string;
  created_at: string;
  updated_at: string | null;
}

export interface CreateRemetenteRequest {
  name: string;
}

export interface UpdateRemetenteRequest {
  name?: string;
}

export interface Destinatario {
  id: string;
  name: string;
  status: string;
  created_at: string;
  updated_at: string | null;
}

export interface CreateDestinatarioRequest {
  name: string;
}

export interface UpdateDestinatarioRequest {
  name?: string;
}

export interface Transportadora {
  id: string;
  name: string;
  status: string;
  created_at: string;
  updated_at: string | null;
}

export interface CreateTransportadoraRequest {
  name: string;
}

export interface UpdateTransportadoraRequest {
  name?: string;
}

