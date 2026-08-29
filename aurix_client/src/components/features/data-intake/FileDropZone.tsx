'use client';

import React, { useState, useRef } from 'react';
import { UploadCloud, FileSpreadsheet, AlertCircle } from 'lucide-react';
import { AurixButton } from '@/components/ui/AurixButton';

interface FileDropZoneProps {
  onFileSelected: (file: File) => void;
  disabled?: boolean;
}

export const FileDropZone: React.FC<FileDropZoneProps> = ({ onFileSelected, disabled = false }) => {
  const [isDragOver, setIsDragOver] = useState(false);
  const [formatError, setFormatError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const validateAndEmit = (file: File) => {
    setFormatError(null);
    const validExtensions = ['.csv', '.xlsx', '.xls', '.parquet'];
    const hasValidExt = validExtensions.some((ext) => file.name.toLowerCase().endsWith(ext));

    if (!hasValidExt) {
      setFormatError('Unsupported file format. Please upload a structured .CSV, .XLSX, or .PARQUET dataset.');
      return;
    }
    onFileSelected(file);
  };

  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragOver(false);
    if (disabled) return;

    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      validateAndEmit(e.dataTransfer.files[0]);
    }
  };

  return (
    <div className="w-full">
      <div
        onDragOver={(e) => {
          e.preventDefault();
          if (!disabled) setIsDragOver(true);
        }}
        onDragLeave={() => setIsDragOver(false)}
        onDrop={handleDrop}
        onClick={() => {
          if (!disabled) fileInputRef.current?.click();
        }}
        className={`relative w-full rounded-2xl p-10 border-2 border-dashed transition-all duration-300 flex flex-col items-center justify-center text-center cursor-pointer select-none overflow-hidden ${
          isDragOver
            ? 'border-[#D4AF37] bg-[#B8912A]/10 shadow-[0_0_40px_rgba(212,175,55,0.2)]'
            : 'border-white/[0.12] bg-[#0C0E12]/80 hover:border-white/25 hover:bg-[#15171A]/60 shadow-[inset_0_1px_1px_rgba(255,255,255,0.05)]'
        } ${disabled ? 'opacity-50 cursor-not-allowed pointer-events-none' : ''}`}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept=".csv,.xlsx,.xls,.parquet"
          className="hidden"
          onChange={(e) => {
            if (e.target.files && e.target.files.length > 0) {
              validateAndEmit(e.target.files[0]);
            }
          }}
        />

        <div className="absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-[#D4AF37]/40 to-transparent pointer-events-none" />

        <div className="relative mb-5 flex items-center justify-center">
          <div className="absolute inset-0 bg-[#B8912A]/20 blur-xl rounded-full animate-pulse" />
          <div className="relative w-16 h-16 rounded-2xl bg-[#15171A] border border-white/10 flex items-center justify-center text-[#D4AF37] shadow-[0_0_20px_rgba(212,175,55,0.15)]">
            <UploadCloud className="w-8 h-8" />
          </div>
        </div>

        <h3 className="text-lg font-bold text-white tracking-wide">
          Give AURIX Your Operational Data
        </h3>
        <p className="text-xs font-mono text-slate-400 mt-1.5 max-w-md">
          Drag and drop enterprise demand logs, inventory ledgers, or supplier receipts to trigger automated pipeline execution.
        </p>

        <div className="flex items-center gap-2.5 mt-6 text-[10px] font-mono text-slate-400">
          <span className="px-2.5 py-1 rounded bg-white/[0.04] border border-white/[0.08] flex items-center gap-1.5">
            <FileSpreadsheet className="w-3 h-3 text-gold" /> CSV
          </span>
          <span className="px-2.5 py-1 rounded bg-white/[0.04] border border-white/[0.08] flex items-center gap-1.5">
            <FileSpreadsheet className="w-3 h-3 text-[#D4AF37]" /> XLSX
          </span>
          <span className="px-2.5 py-1 rounded bg-white/[0.04] border border-white/[0.08] flex items-center gap-1.5">
            <FileSpreadsheet className="w-3 h-3 text-gold" /> PARQUET
          </span>
        </div>

        <div className="mt-6">
          <AurixButton variant="primary" size="sm" type="button">
            BROWSE LOCAL STORAGE
          </AurixButton>
        </div>
      </div>

      {formatError && (
        <div className="mt-3 p-3 rounded-lg bg-[#FF6B6B]/10 border border-[#FF6B6B]/30 flex items-center gap-2.5 text-xs font-mono text-[#FF8585]">
          <AlertCircle className="w-4 h-4 shrink-0" />
          <span>{formatError}</span>
        </div>
      )}
    </div>
  );
};