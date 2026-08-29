import {
  IngestionMetadata,
  ColumnMappingItem,
  DataInspectionRow,
  ValidationIssue,
} from '@/types/data-intake.types';

const AURIX_CANONICAL_FIELDS = [
  { canonicalKey: 'sku_id', canonicalName: 'SKU / Item Identifier', canonicalLabel: 'SKU / Item Identifier', required: true, dataType: 'STRING' },
  { canonicalKey: 'location_id', canonicalName: 'Warehouse / Facility ID', canonicalLabel: 'Warehouse / Facility ID', required: true, dataType: 'STRING' },
  { canonicalKey: 'date', canonicalName: 'Transaction / Snapshot Date', canonicalLabel: 'Transaction / Snapshot Date', required: true, dataType: 'DATE' },
  { canonicalKey: 'demand_qty', canonicalName: 'Demand Quantity', canonicalLabel: 'Demand Quantity', required: false, dataType: 'FLOAT' },
  { canonicalKey: 'inventory_qty', canonicalName: 'Closing On-Hand Stock', canonicalLabel: 'Closing On-Hand Stock', required: false, dataType: 'FLOAT' },
  { canonicalKey: 'unit_cost', canonicalName: 'Unit Acquisition Cost', canonicalLabel: 'Unit Acquisition Cost', required: false, dataType: 'CURRENCY_INR' },
];

export class DataIntakeAdapter {
  public static generateSimulatedMapping(file: File): {
    metadata: IngestionMetadata;
    mappings: ColumnMappingItem[];
    previewRows: DataInspectionRow[];
    validationIssues: ValidationIssue[];
  } {
    const metadata: IngestionMetadata = {
      fileId: `FILE-${Date.now()}`,
      fileName: file.name,
      fileSize: `${(file.size / 1024).toFixed(1)} KB`,
      fileSizeBytes: file.size,
      rowCount: 14250,
      columnCount: 8,
      detectedDatasetType: 'OPERATIONAL_TRANSACTIONS',
      detectedDomain: 'INVENTORY_DEMAND',
      uploadedAt: new Date().toISOString(),
      checksum: 'sha256:0x89f2a7b3c4d5e6f1',
    };

    const mappings: ColumnMappingItem[] = AURIX_CANONICAL_FIELDS.map((canon) => {
      const isMapped = true;
      return {
        canonicalKey: canon.canonicalKey,
        canonicalName: canon.canonicalName,
        canonicalLabel: canon.canonicalLabel,
        required: canon.required,
        detectedColumn: isMapped ? canon.canonicalKey : null,
        confidence: 'exact',
        dataType: canon.dataType,
        sampleValue: canon.dataType === 'FLOAT' ? 140.0 : canon.dataType === 'DATE' ? '2026-08-20' : 'SKU-004',
        status: 'valid',
      };
    });

    const previewRows: DataInspectionRow[] = [
      {
        sku_id: 'SKU-004',
        location_id: 'BLR_CENTRAL_DC',
        date: '2026-08-20',
        demand_qty: 120,
        inventory_qty: 450,
        unit_cost: 198.5,
      },
      {
        sku_id: 'SKU-005',
        location_id: 'DEL_NORTH_HUB',
        date: '2026-08-20',
        demand_qty: 85,
        inventory_qty: 210,
        unit_cost: 245.0,
      },
    ];

    const validationIssues: ValidationIssue[] = [
      {
        id: 'ISSUE-01',
        severity: 'info',
        field: 'date',
        message: 'Temporal resolution verified at daily bucket frequency.',
        remediationSuggestion: 'Ready for deterministic forecasting and EDA.',
      },
    ];

    return {
      metadata,
      mappings,
      previewRows,
      validationIssues,
    };
  }
}