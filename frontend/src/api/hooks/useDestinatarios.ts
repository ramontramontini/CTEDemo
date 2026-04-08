import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '../apiService';
import { queryKeys } from './queryKeys';
import type { CreateDestinatarioRequest, UpdateDestinatarioRequest } from '../../types';

export function useDestinatarios() {
  return useQuery({
    queryKey: queryKeys.destinatarios.all,
    queryFn: api.listDestinatarios,
  });
}

export function useDestinatario(id: string) {
  return useQuery({
    queryKey: queryKeys.destinatarios.detail(id),
    queryFn: () => api.getDestinatario(id),
    enabled: !!id,
  });
}

export function useCreateDestinatario() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: CreateDestinatarioRequest) => api.createDestinatario(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.destinatarios.all });
    },
  });
}

export function useUpdateDestinatario() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: UpdateDestinatarioRequest }) => api.updateDestinatario(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.destinatarios.all });
    },
  });
}

export function useDeleteDestinatario() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => api.deleteDestinatario(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.destinatarios.all });
    },
  });
}
