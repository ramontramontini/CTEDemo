# CTEDemo Domain Overview

## Sistema Gerador e Gerenciador de CT-e

### Objetivo
Motor de geracao de CT-e que transforma dados de pedidos de frete (entrada JSON) em documentos fiscais eletronicos validos no formato XML v4.00.

### Escopo Inicial
- Sem integracao com sistemas externos (SEFAZ, etc.)
- Sem filas de mensagens
- Foco na geracao e validacao do XML

### Aggregates

```
cte/ ──────── CT-e document lifecycle (core)
remetente/ ── Sender/shipper
destinatario/ Recipient
transportadora/ Carrier
shared/ ───── Cross-aggregate VOs (CNPJ, CPF, UF, Money, ChaveAcesso)
services/ ─── Cross-aggregate orchestration (CTeGeneratorService)
```

### Dependency Graph
```
shared/ <── cte/ <── services/
  ^           ^
  |           |
  ├── remetente/
  ├── destinatario/
  └── transportadora/
```
