# L3 Domain — CTEDemo (Auto-Loaded)

> CT-e (Conhecimento de Transporte Eletronico) domain rules.
> Full domain rules: `docs/domain/`

---

## Domain Overview

**CTEDemo** generates and manages CT-e (electronic freight transport documents):
- **CT-e** — Main fiscal document: transforms freight order JSON into XML v4.00
- **Remetente** — Sender/shipper entity
- **Destinatario** — Recipient entity
- **Transportadora** — Carrier entity
- **Carga** — Cargo/freight details

---

## Key Business Rules

- CT-e follows SEFAZ XML schema v4.00 (layout `cte_v4.00.xsd`)
- CNPJ/CPF validation mandatory for all fiscal entities
- Chave de acesso (access key) = 44-digit numeric key, algorithmically generated
- Modal types: Rodoviario (road), Aereo (air), Aquaviario (water), Ferroviario (rail), Dutoviario (pipeline)
- CFOP codes determine fiscal operation nature
- CST/CSOSN codes determine tax regime
- ICMS calculation varies by UF origin/destination
- CT-e status lifecycle: em_digitacao -> autorizado -> cancelado | inutilizado

---

## CT-e XML Structure (v4.00)

```xml
<CTe>
  <infCte>
    <ide/>           <!-- Identification: UF, series, number, modal -->
    <compl/>         <!-- Complementary data -->
    <emit/>          <!-- Emitter (carrier) -->
    <rem/>           <!-- Sender (shipper) -->
    <dest/>          <!-- Recipient -->
    <vPrest/>        <!-- Service value -->
    <imp/>           <!-- Taxes (ICMS) -->
    <infCTeNorm>
      <infCarga/>    <!-- Cargo info -->
      <infDoc/>      <!-- Referenced documents (NF-e) -->
      <infModal/>    <!-- Modal-specific data -->
    </infCTeNorm>
  </infCte>
  <Signature/>       <!-- Digital signature (future) -->
</CTe>
```

---

## Aggregates

| Aggregate | Responsibility |
|-----------|---------------|
| `cte/` | CT-e generation, validation, XML serialization, status lifecycle |
| `remetente/` | Sender entity, address, CNPJ/CPF |
| `destinatario/` | Recipient entity, address, CNPJ/CPF |
| `transportadora/` | Carrier entity, RNTRC, modal capabilities |
| `shared/` | CNPJ, CPF, UF, Money, ChaveAcesso value objects |

---

## Validation Rules

- CNPJ: 14 digits + 2 check digits (mod 11 algorithm)
- CPF: 11 digits + 2 check digits (mod 11 algorithm)
- Chave de acesso: cUF + AAMM + CNPJ + mod + serie + nCT + tpEmis + cCT + cDV
- CFOP: 4-digit code, first digit = operation direction (5=intra, 6=inter, 7=export)
- Weight/value: positive, non-zero for cargo
- UF codes: IBGE 2-digit state codes (11-53)
