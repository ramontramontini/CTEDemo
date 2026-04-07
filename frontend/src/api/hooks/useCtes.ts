import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '../apiService';
import { queryKeys } from './queryKeys';

export function useCtes() {
  return useQuery({
    queryKey: queryKeys.ctes.all,
    queryFn: api.listCtes,
  });
}

export function useCte(id: string) {
  return useQuery({
    queryKey: queryKeys.ctes.detail(id),
    queryFn: () => api.getCte(id),
    enabled: !!id,
  });
}

export function useGenerateCte() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: Record<string, unknown>) => api.generateCte(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.ctes.all });
    },
  });
}
