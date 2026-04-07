# CTEDemo Domain Overview

## Aggregates

### Cte

CT-e (Conhecimento de Transporte Eletrônico) — Brazilian electronic transport document generation.

- **Entity:** `cte/entity.py` — Aggregate root with `access_key`, `freight_order_number`, `status`, `xml`, `original_payload`. Behavior: `is_gerado()`, `formatted_access_key()`
- **Home:** `cte/home.py` — `CteHome.generate(payload)` orchestrates FreightOrder validation → AccessKey generation → XML build → entity creation
- **Value Objects:** `cte/value_objects.py` — `AccessKey` (44-digit with mod11 DV), `FreightOrder`/`FreightOrderFolder`/`FreightOrderTax` (input parsing + validation)
- **XML Builder:** `cte/xml_builder.py` — Builds CT-e XML v4.00 structure (identification, parties, values, taxes, cargo, modal)
- **Enums:** `cte/enums.py` — `CteStatus.GERADO`, `CteStatus.ERRO`
- **Repository:** `cte/repository.py`

### Shared Value Objects

Cross-aggregate immutable types in `domain/shared/`:

- **Cnpj** (`shared/cnpj.py`) — 14-digit CNPJ with módulo 11 DV validation
- **Cpf** (`shared/cpf.py`) — 11-digit CPF with módulo 11 DV validation
- **VehiclePlate** (`shared/vehicle_plate.py`) — Old format (ABC1234) + Mercosul format (ABC1D23)

### Remetente

- **Entity:** `remetente/entity.py`
- **Home:** `remetente/home.py`
- **Repository:** `remetente/repository.py`

### Destinatario

- **Entity:** `destinatario/entity.py`
- **Home:** `destinatario/home.py`
- **Repository:** `destinatario/repository.py`

### Transportadora

- **Entity:** `transportadora/entity.py`
- **Home:** `transportadora/home.py`
- **Repository:** `transportadora/repository.py`

## Dependencies

> TODO: Define aggregate dependency graph
