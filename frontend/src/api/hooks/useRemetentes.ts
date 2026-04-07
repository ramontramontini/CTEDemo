import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '../apiService';
import { queryKeys } from './queryKeys';
import type { CreateRemetenteRequest, UpdateRemetenteRequest } from '../../types';

export function useRemetentes() {
  return useQuery({
    queryKey: queryKeys.remetentes.all,
    queryFn: api.listRemetentes,
  });
}

export function useRemetente(id: string) {
  return useQuery({
    queryKey: queryKeys.remetentes.detail(id),
    queryFn: () => api.getRemetente(id),
    enabled: !!id,
  });
}

export function useCreateRemetente() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: CreateRemetenteRequest) => api.createRemetente(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.remetentes.all });
    },
  });
}

export function useUpdateRemetente() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: UpdateRemetenteRequest }) => api.updateRemetente(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.remetentes.all });
    },
  });
}

export function useDeleteRemetente() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => api.deleteRemetente(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.remetentes.all });
    },
  });
}
