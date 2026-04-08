# CTEDemo Domain Overview

## Aggregates

### Cte

CT-e (Conhecimento de Transporte Eletrônico) — Brazilian electronic transport document generation.

- **Entity:** `cte/entity.py` — Aggregate root with `access_key`, `freight_order_number`, `status`, `xml`, `original_payload`. Behavior: `is_gerado()`, `formatted_access_key()`
- **Home:** `cte/home.py` — `CteHome.generate(payload, transportadora, remetente?, destinatario?)` orchestrates FreightOrder validation → AccessKey generation → XML build → entity creation. Requires `Transportadora` for `<emit>`, optionally accepts `Remetente` for `<rem>` enrichment and `Destinatario` for `<dest>` section
- **Value Objects:** `cte/value_objects.py` — `AccessKey` (44-digit with mod11 DV), `FreightOrder`/`FreightOrderFolder`/`FreightOrderTax` (input parsing + validation)
- **XML Builder:** `cte/xml_builder.py` — Builds CT-e XML v4.00 structure: `<ide>`, `<compl>`, `<emit>` (Transportadora), `<rem>` (Remetente), `<dest>` (Destinatario), `<vPrest>`, `<imp>` (per-tax-type: ICMS with CST groups, COFINS, PIS + vTotTrib), `<infCTeNorm>` (cargo, NF-e refs, modal with vehicle + trailer plates)
- **CFOP Validator:** `cte/cfop_validator.py` — Geographic validation: 5xxx requires same-state, 6xxx requires cross-state origin/destination
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

### Nfe

NF-e (Nota Fiscal Eletrônica) — mock repository for related NF-e validation during CT-e generation.

- **Entity:** `nfe/entity.py` — Lightweight frozen dataclass: `key` (44-digit access key), `status` ("authorized"/"canceled"), `emitter_cnpj`
- **Repository:** `nfe/repository.py` — Abstract interface with `find_by_key()`, `find_all()`
- **Memory Impl:** 3 seed records — authorized (matching CNPJ), canceled, authorized (divergent emitter)

### Services (Cross-Aggregate Orchestration)

- **CteGenerationService:** `services/cte_generation_service.py` — Orchestrates Transportadora/Remetente/Destinatario lookup + CT-e generation. Validates carrier CNPJ exists in Transportadora registry, optionally resolves Remetente (by CNPJ_Origin) and Destinatario (by CNPJ_Dest) for XML enrichment, then delegates to `CteHome.generate()`. Keeps Home infrastructure-free per L1 cross-aggregate rules
- **NfeValidationService:** `services/nfe_validation_service.py` — Validates NF-e keys exist and are authorized. Unknown/canceled keys raise ValueError (400). CNPJ divergence between NF-e emitter and CNPJ_Origin returns non-blocking warnings

## Dependencies

- **Cte → Transportadora:** CT-e generation requires a registered Transportadora (carrier lookup via `CteGenerationService`) for `<emit>` XML enrichment
- **Cte → Remetente:** Optional — `<rem>` section enriched with Remetente entity data (xNome, IE, enderRem) when CNPJ_Origin matches a registered Remetente. Falls back to CNPJ-only stub
- **Cte → Destinatario:** Optional — `<dest>` section built from Destinatario entity when CNPJ_Dest provided. Also used for CFOP geographic validation (skipped when no `CNPJ_Dest`)
- **Cte → Nfe:** Related NF-e validation — keys in `RelatedNFE` checked against NF-e repository (unknown/canceled → 400, emitter CNPJ divergence → warning)
