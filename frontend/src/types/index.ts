/**
 * TypeScript interfaces mirroring backend DTOs.
 */

export interface Cte {
  id: string;
  cTeKey: string;
  formattedAccessKey: string;
  freightOrderNumber: string;
  status: string;
  erp: string;
  documentType: string;
  totalFolders: number;
  xml: string;
  createdAt: string;
  updatedAt: string;
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

export interface ProblemDetail {
  type: string;
  title: string;
  status: number;
  detail: string;
  errors?: Record<string, string>;
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
  cnpj: string | null;
  cpf: string | null;
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

export interface CreateDestinatarioRequest {
  cnpj?: string;
  cpf?: string;
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

export interface UpdateDestinatarioRequest {
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

export interface Transportadora {
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

export interface CreateTransportadoraRequest {
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

export interface UpdateTransportadoraRequest {
  cnpj?: string;
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

