export const SAMPLE_PAYLOAD = {
  FreightOrder: "12345678901234",
  ERP: "SAP",
  Carrier: "16003754000135",
  CNPJ_Origin: "03026527000183",
  Incoterms: "CIF",
  OperationType: "0",
  Folder: [
    {
      FolderNumber: "001",
      ReferenceNumber: "REF001",
      NetValue: 1500.00,
      VehiclePlate: "ABC1D23",
      TrailerPlate: [],
      VehicleAxles: "2",
      EquipmentType: "TRUCK",
      Weight: 5000.00,
      CFOP: "6352",
      DriverID: "12345678909",
      Cancel: false,
      Tax: [
        {
          TaxType: "ICMS",
          Base: 1500.00,
          Rate: 12.00,
          Value: 180.00,
          TaxCode: "00",
          ReducedBase: 0,
        },
      ],
      RelatedNFE: ["35251003026527000183550010013119001683587366"],
    },
  ],
};
