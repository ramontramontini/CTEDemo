import { useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '../apiService';

export function useResetData() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => api.resetData(),
    onSuccess: () => {
      queryClient.invalidateQueries();
    },
  });
}
