/**
 * TypeScript interfaces mirroring backend DTOs.
 */

export interface Cte {
  id: string;
  access_key: string;
  formatted_access_key: string;
  freight_order_number: string;
  status: string;
  xml: string;
  created_at: string;
}

export interface GenerateCteRequest {
  FreightOrder: string;
  ERP: string;
  Carrier: string;
  CNPJ_Origin: string;
  Incoterms: string;
  OperationType: string;
  Folder: Record<string, unknown>[];
}

export interface ValidationError {
  field: string;
  message: string;
}

export interface Remetente {
  id: string;
  cnpj: string;
  razao_social: string;
  nome_fantasia: string;
  ie: string;
  uf: string;
  cidade: string;
  logradouro: string;
  numero: string;
  bairro: string;
  cep: string;
  status: string;
  created_at: string;
  updated_at: string | null;
}

export interface CreateRemetenteRequest {
  cnpj: string;
  razao_social: string;
  nome_fantasia?: string;
  ie?: string;
  uf: string;
  cidade: string;
  logradouro: string;
  numero: string;
  bairro: string;
  cep: string;
}

export interface UpdateRemetenteRequest {
  razao_social?: string;
  nome_fantasia?: string;
  ie?: string;
  uf?: string;
  cidade?: string;
  logradouro?: string;
  numero?: string;
  bairro?: string;
  cep?: string;
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

