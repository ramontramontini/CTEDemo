import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '../apiService';
import { queryKeys } from './queryKeys';
import type { CreateTransportadoraRequest } from '../../types';

export function useTransportadoras() {
  return useQuery({
    queryKey: queryKeys.transportadoras.all,
    queryFn: api.listTransportadoras,
  });
}

export function useTransportadora(id: string) {
  return useQuery({
    queryKey: queryKeys.transportadoras.detail(id),
    queryFn: () => api.getTransportadora(id),
    enabled: !!id,
  });
}

export function useCreateTransportadora() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: CreateTransportadoraRequest) => api.createTransportadora(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.transportadoras.all });
    },
  });
}
