export interface Scenario {
  id: string;
  name: string;
  description: string;
  category: 'success' | 'business_error' | 'validation_error' | 'cfop_error';
  expectedStatus: 201 | 400 | 422;
  expectedOutcome: string;
  payload: Record<string, unknown>;
}

export const SCENARIO_CATEGORIES: Record<
  Scenario['category'],
  { label: string; color: string }
> = {
  success: { label: 'Sucesso', color: 'green' },
  business_error: { label: 'Erro de Negocio', color: 'orange' },
  validation_error: { label: 'Erro de Validacao', color: 'red' },
  cfop_error: { label: 'Erro CFOP', color: 'red' },
};

// Seed data constants (must match backend memory repositories)
const CARRIER_SP = '16003754000135'; // Transportadora Postman Ltda, UF: SP
const CARRIER_RJ = '33014556000196'; // Log Express SA, UF: RJ
const REMETENTE_SP = '03026527000183'; // Remetente Postman Ltda, UF: SP
const REMETENTE_RJ = '11444777000161'; // Industria XYZ SA, UF: RJ
const DEST_PE = '44555666000181'; // Comercio Recife Ltda, UF: PE
const NFE_AUTHORIZED = '35251003026527000183550010013119001683587366';
const NFE_AUTHORIZED_2 = '35251003026527000183550010013119001683587367';
const NFE_CANCELED = '35230410758386000159550010000000021000000022';
const NFE_DIVERGENT = '31230499888777000166550010000000031000000039'; // emitter: 99888777000166

function basePayload(freightOrder: string): Record<string, unknown> {
  return {
    FreightOrder: freightOrder,
    ERP: 'SAP',
    Carrier: CARRIER_SP,
    CNPJ_Origin: REMETENTE_SP,
    Incoterms: 'CIF',
    OperationType: '0',
    Folder: [
      {
        FolderNumber: '001',
        ReferenceNumber: 'REF001',
        NetValue: 1500.0,
        VehiclePlate: 'ABC1D23',
        TrailerPlate: [],
        VehicleAxles: '2',
        EquipmentType: 'TRUCK',
        Weight: 5000.0,
        CFOP: '6352',
        DriverID: '12345678909',
        Cancel: false,
        Tax: [
          {
            TaxType: 'ICMS',
            Base: 1500.0,
            Rate: 12.0,
            Value: 180.0,
            TaxCode: '00',
            ReducedBase: 0,
          },
        ],
        RelatedNFE: [NFE_AUTHORIZED],
      },
    ],
  };
}

export const SCENARIOS: Scenario[] = [
  // ── Success ──────────────────────────────────────────────
  {
    id: 'happy-path',
    name: 'Cenario feliz',
    description: 'Payload valido completo — CT-e gerado com sucesso',
    category: 'success',
    expectedStatus: 201,
    expectedOutcome: '201 — CT-e gerado com status GERADO',
    payload: basePayload('SC01000000000001'),
  },
  {
    id: 'nfe-cnpj-divergence',
    name: 'Divergencia CNPJ NF-e',
    description: 'NF-e emitente com CNPJ diferente do CNPJ_Origin — gera warning',
    category: 'success',
    expectedStatus: 201,
    expectedOutcome: '201 — CT-e gerado com warning de divergencia de CNPJ',
    payload: {
      ...basePayload('SC02000000000002'),
      Folder: [
        {
          FolderNumber: '001',
          ReferenceNumber: 'REF001',
          NetValue: 1500.0,
          VehiclePlate: 'ABC1D23',
          TrailerPlate: [],
          VehicleAxles: '2',
          EquipmentType: 'TRUCK',
          Weight: 5000.0,
          CFOP: '6352',
          DriverID: '12345678909',
          Cancel: false,
          Tax: [
            {
              TaxType: 'ICMS',
              Base: 1500.0,
              Rate: 12.0,
              Value: 180.0,
              TaxCode: '00',
              ReducedBase: 0,
            },
          ],
          RelatedNFE: [NFE_DIVERGENT],
        },
      ],
    },
  },

  // ── Business Errors (400) ────────────────────────────────
  {
    id: 'duplicate-freight-order',
    name: 'Ordem duplicada',
    description:
      'FreightOrder ja utilizado — execute o cenario feliz primeiro, depois este',
    category: 'business_error',
    expectedStatus: 400,
    expectedOutcome: '400 — Duplicate FreightOrder (execute o cenario feliz antes)',
    payload: basePayload('SC01000000000001'),
  },
  {
    id: 'carrier-not-found',
    name: 'Transportadora nao encontrada',
    description: 'CNPJ de Carrier nao cadastrado no sistema',
    category: 'business_error',
    expectedStatus: 400,
    expectedOutcome: '400 — Transportadora not found for CNPJ',
    payload: {
      ...basePayload('SC04000000000004'),
      Carrier: '11222333000181', // valid CNPJ format but not in seed data
    },
  },
  {
    id: 'nfe-not-found',
    name: 'NF-e nao encontrada',
    description: 'Chave de NF-e desconhecida — nao existe no repositorio',
    category: 'business_error',
    expectedStatus: 400,
    expectedOutcome: '400 — NF-e not found',
    payload: {
      ...basePayload('SC05000000000005'),
      Folder: [
        {
          FolderNumber: '001',
          ReferenceNumber: 'REF001',
          NetValue: 1500.0,
          VehiclePlate: 'ABC1D23',
          TrailerPlate: [],
          VehicleAxles: '2',
          EquipmentType: 'TRUCK',
          Weight: 5000.0,
          CFOP: '6352',
          DriverID: '12345678909',
          Cancel: false,
          Tax: [
            {
              TaxType: 'ICMS',
              Base: 1500.0,
              Rate: 12.0,
              Value: 180.0,
              TaxCode: '00',
              ReducedBase: 0,
            },
          ],
          RelatedNFE: ['99999999999999999999999999999999999999999999'],
        },
      ],
    },
  },
  {
    id: 'nfe-canceled',
    name: 'NF-e cancelada',
    description: 'Chave de NF-e com status cancelado',
    category: 'business_error',
    expectedStatus: 400,
    expectedOutcome: '400 — NF-e canceled',
    payload: {
      ...basePayload('SC06000000000006'),
      Folder: [
        {
          FolderNumber: '001',
          ReferenceNumber: 'REF001',
          NetValue: 1500.0,
          VehiclePlate: 'ABC1D23',
          TrailerPlate: [],
          VehicleAxles: '2',
          EquipmentType: 'TRUCK',
          Weight: 5000.0,
          CFOP: '6352',
          DriverID: '12345678909',
          Cancel: false,
          Tax: [
            {
              TaxType: 'ICMS',
              Base: 1500.0,
              Rate: 12.0,
              Value: 180.0,
              TaxCode: '00',
              ReducedBase: 0,
            },
          ],
          RelatedNFE: [NFE_CANCELED],
        },
      ],
    },
  },

  // ── Validation Errors (422) ──────────────────────────────
  {
    id: 'invalid-carrier-cnpj',
    name: 'CNPJ Carrier invalido',
    description: 'Digito verificador do CNPJ do Carrier incorreto',
    category: 'validation_error',
    expectedStatus: 422,
    expectedOutcome: '422 — CNPJ invalido (digito verificador)',
    payload: {
      ...basePayload('SC07000000000007'),
      Carrier: '16003754000199', // bad check digit
    },
  },
  {
    id: 'invalid-driver-cpf',
    name: 'CPF motorista invalido',
    description: 'Digito verificador do CPF do DriverID incorreto',
    category: 'validation_error',
    expectedStatus: 422,
    expectedOutcome: '422 — CPF invalido (digito verificador)',
    payload: {
      ...basePayload('SC08000000000008'),
      Folder: [
        {
          FolderNumber: '001',
          ReferenceNumber: 'REF001',
          NetValue: 1500.0,
          VehiclePlate: 'ABC1D23',
          TrailerPlate: [],
          VehicleAxles: '2',
          EquipmentType: 'TRUCK',
          Weight: 5000.0,
          CFOP: '6352',
          DriverID: '12345678900', // bad check digit
          Cancel: false,
          Tax: [
            {
              TaxType: 'ICMS',
              Base: 1500.0,
              Rate: 12.0,
              Value: 180.0,
              TaxCode: '00',
              ReducedBase: 0,
            },
          ],
          RelatedNFE: [NFE_AUTHORIZED],
        },
      ],
    },
  },
  {
    id: 'invalid-vehicle-plate',
    name: 'Placa invalida',
    description: 'Formato de placa nao reconhecido (nem antigo nem Mercosul)',
    category: 'validation_error',
    expectedStatus: 422,
    expectedOutcome: '422 — Placa invalida (formato)',
    payload: {
      ...basePayload('SC09000000000009'),
      Folder: [
        {
          FolderNumber: '001',
          ReferenceNumber: 'REF001',
          NetValue: 1500.0,
          VehiclePlate: 'INVALID',
          TrailerPlate: [],
          VehicleAxles: '2',
          EquipmentType: 'TRUCK',
          Weight: 5000.0,
          CFOP: '6352',
          DriverID: '12345678909',
          Cancel: false,
          Tax: [
            {
              TaxType: 'ICMS',
              Base: 1500.0,
              Rate: 12.0,
              Value: 180.0,
              TaxCode: '00',
              ReducedBase: 0,
            },
          ],
          RelatedNFE: [NFE_AUTHORIZED],
        },
      ],
    },
  },
  {
    id: 'missing-freight-order',
    name: 'FreightOrder ausente',
    description: 'Campo FreightOrder omitido do payload',
    category: 'validation_error',
    expectedStatus: 422,
    expectedOutcome: '422 — Campo obrigatorio ausente',
    payload: (() => {
      const p = basePayload('SC10000000000010');
      delete p.FreightOrder;
      return p;
    })(),
  },
  {
    id: 'extra-field',
    name: 'Campo extra no payload',
    description: 'Payload contem campo nao esperado pelo schema',
    category: 'validation_error',
    expectedStatus: 422,
    expectedOutcome: '422 — Extra inputs are not permitted',
    payload: {
      ...basePayload('SC11000000000011'),
      CampoInexistente: 'valor',
    },
  },
  {
    id: 'invalid-incoterms',
    name: 'Incoterms invalido',
    description: 'Valor de Incoterms diferente de CIF ou FOB',
    category: 'validation_error',
    expectedStatus: 422,
    expectedOutcome: '422 — Incoterms deve ser CIF ou FOB',
    payload: {
      ...basePayload('SC12000000000012'),
      Incoterms: 'EXW',
    },
  },
  {
    id: 'invalid-operation-type',
    name: 'OperationType invalido',
    description: 'Valor de OperationType fora de 0, 1, 2, 3',
    category: 'validation_error',
    expectedStatus: 422,
    expectedOutcome: '422 — OperationType deve ser 0, 1, 2 ou 3',
    payload: {
      ...basePayload('SC13000000000013'),
      OperationType: '9',
    },
  },
  {
    id: 'tax-calculation-mismatch',
    name: 'Calculo de imposto incorreto',
    description: 'Value nao corresponde a Base * Rate / 100',
    category: 'validation_error',
    expectedStatus: 422,
    expectedOutcome: '422 — Tax value mismatch (base * rate / 100)',
    payload: {
      ...basePayload('SC14000000000014'),
      Folder: [
        {
          FolderNumber: '001',
          ReferenceNumber: 'REF001',
          NetValue: 1500.0,
          VehiclePlate: 'ABC1D23',
          TrailerPlate: [],
          VehicleAxles: '2',
          EquipmentType: 'TRUCK',
          Weight: 5000.0,
          CFOP: '6352',
          DriverID: '12345678909',
          Cancel: false,
          Tax: [
            {
              TaxType: 'ICMS',
              Base: 1500.0,
              Rate: 12.0,
              Value: 999.99, // Should be 180.00
              TaxCode: '00',
              ReducedBase: 0,
            },
          ],
          RelatedNFE: [NFE_AUTHORIZED],
        },
      ],
    },
  },
  {
    id: 'duplicate-folder-number',
    name: 'FolderNumber duplicado',
    description: 'Duas pastas com o mesmo FolderNumber no mesmo payload',
    category: 'validation_error',
    expectedStatus: 422,
    expectedOutcome: '422 — Duplicate FolderNumber',
    payload: {
      ...basePayload('SC15000000000015'),
      Folder: [
        {
          FolderNumber: '001',
          ReferenceNumber: 'REF001',
          NetValue: 1500.0,
          VehiclePlate: 'ABC1D23',
          TrailerPlate: [],
          VehicleAxles: '2',
          EquipmentType: 'TRUCK',
          Weight: 5000.0,
          CFOP: '6352',
          DriverID: '12345678909',
          Cancel: false,
          Tax: [
            {
              TaxType: 'ICMS',
              Base: 1500.0,
              Rate: 12.0,
              Value: 180.0,
              TaxCode: '00',
              ReducedBase: 0,
            },
          ],
          RelatedNFE: [NFE_AUTHORIZED],
        },
        {
          FolderNumber: '001', // duplicate
          ReferenceNumber: 'REF002',
          NetValue: 2000.0,
          VehiclePlate: 'DEF2E34',
          TrailerPlate: [],
          VehicleAxles: '3',
          EquipmentType: 'TRUCK',
          Weight: 8000.0,
          CFOP: '6352',
          DriverID: '12345678909',
          Cancel: false,
          Tax: [
            {
              TaxType: 'ICMS',
              Base: 2000.0,
              Rate: 12.0,
              Value: 240.0,
              TaxCode: '00',
              ReducedBase: 0,
            },
          ],
          RelatedNFE: [NFE_AUTHORIZED_2],
        },
      ],
    },
  },
  {
    id: 'invalid-nfe-key-format',
    name: 'Chave NF-e formato invalido',
    description: 'Chave de NF-e com menos de 44 digitos',
    category: 'validation_error',
    expectedStatus: 422,
    expectedOutcome: '422 — NF-e key must be exactly 44 numeric digits',
    payload: {
      ...basePayload('SC16000000000016'),
      Folder: [
        {
          FolderNumber: '001',
          ReferenceNumber: 'REF001',
          NetValue: 1500.0,
          VehiclePlate: 'ABC1D23',
          TrailerPlate: [],
          VehicleAxles: '2',
          EquipmentType: 'TRUCK',
          Weight: 5000.0,
          CFOP: '6352',
          DriverID: '12345678909',
          Cancel: false,
          Tax: [
            {
              TaxType: 'ICMS',
              Base: 1500.0,
              Rate: 12.0,
              Value: 180.0,
              TaxCode: '00',
              ReducedBase: 0,
            },
          ],
          RelatedNFE: ['12345'],
        },
      ],
    },
  },
  {
    id: 'negative-net-value',
    name: 'NetValue negativo',
    description: 'Valor de NetValue menor ou igual a zero',
    category: 'validation_error',
    expectedStatus: 422,
    expectedOutcome: '422 — NetValue must be greater than 0',
    payload: {
      ...basePayload('SC17000000000017'),
      Folder: [
        {
          FolderNumber: '001',
          ReferenceNumber: 'REF001',
          NetValue: -100.0,
          VehiclePlate: 'ABC1D23',
          TrailerPlate: [],
          VehicleAxles: '2',
          EquipmentType: 'TRUCK',
          Weight: 5000.0,
          CFOP: '6352',
          DriverID: '12345678909',
          Cancel: false,
          Tax: [
            {
              TaxType: 'ICMS',
              Base: 1500.0,
              Rate: 12.0,
              Value: 180.0,
              TaxCode: '00',
              ReducedBase: 0,
            },
          ],
          RelatedNFE: [NFE_AUTHORIZED],
        },
      ],
    },
  },

  // ── CFOP Errors (422) ────────────────────────────────────
  {
    id: 'cfop-5xxx-cross-state',
    name: 'CFOP 5xxx interestadual',
    description:
      'CFOP 5352 exige mesmo estado, mas Carrier (SP) e Destinatario (PE) sao diferentes',
    category: 'cfop_error',
    expectedStatus: 422,
    expectedOutcome: '422 — CFOP 5xxx requer mesmo estado origem/destino',
    payload: {
      ...basePayload('SC18000000000018'),
      Carrier: CARRIER_SP,
      CNPJ_Dest: DEST_PE, // PE != SP
      Folder: [
        {
          FolderNumber: '001',
          ReferenceNumber: 'REF001',
          NetValue: 1500.0,
          VehiclePlate: 'ABC1D23',
          TrailerPlate: [],
          VehicleAxles: '2',
          EquipmentType: 'TRUCK',
          Weight: 5000.0,
          CFOP: '5352', // requires same state
          DriverID: '12345678909',
          Cancel: false,
          Tax: [
            {
              TaxType: 'ICMS',
              Base: 1500.0,
              Rate: 12.0,
              Value: 180.0,
              TaxCode: '00',
              ReducedBase: 0,
            },
          ],
          RelatedNFE: [NFE_AUTHORIZED],
        },
      ],
    },
  },
  {
    id: 'cfop-6xxx-same-state',
    name: 'CFOP 6xxx intraestadual',
    description:
      'CFOP 6352 exige estados diferentes, mas Carrier (RJ) e Remetente/Origin (RJ) sao iguais',
    category: 'cfop_error',
    expectedStatus: 422,
    expectedOutcome: '422 — CFOP 6xxx requer estados diferentes origem/destino',
    payload: {
      ...basePayload('SC19000000000019'),
      Carrier: CARRIER_RJ, // RJ
      CNPJ_Origin: REMETENTE_RJ, // RJ — same state as carrier
      Folder: [
        {
          FolderNumber: '001',
          ReferenceNumber: 'REF001',
          NetValue: 1500.0,
          VehiclePlate: 'ABC1D23',
          TrailerPlate: [],
          VehicleAxles: '2',
          EquipmentType: 'TRUCK',
          Weight: 5000.0,
          CFOP: '6352', // requires cross-state
          DriverID: '12345678909',
          Cancel: false,
          Tax: [
            {
              TaxType: 'ICMS',
              Base: 1500.0,
              Rate: 12.0,
              Value: 180.0,
              TaxCode: '00',
              ReducedBase: 0,
            },
          ],
          RelatedNFE: [NFE_AUTHORIZED],
        },
      ],
    },
  },
];
