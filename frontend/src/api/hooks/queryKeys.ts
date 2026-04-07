export const queryKeys = {

  ctes: {
    all: ['ctes'] as const,
    detail: (id: string) => ['ctes', id] as const,
  },
  remetentes: {
    all: ['remetentes'] as const,
    detail: (id: string) => ['remetentes', id] as const,
  },
  destinatarios: {
    all: ['destinatarios'] as const,
    detail: (id: string) => ['destinatarios', id] as const,
  },
  transportadoras: {
    all: ['transportadoras'] as const,
    detail: (id: string) => ['transportadoras', id] as const,
  },
};
