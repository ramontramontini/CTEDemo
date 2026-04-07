import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '../apiService';
import { queryKeys } from './queryKeys';
import type { CreateDestinatarioRequest } from '../../types';

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
