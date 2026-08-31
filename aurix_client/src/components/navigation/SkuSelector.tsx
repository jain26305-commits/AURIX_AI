'use client';

import React from 'react';
import {
  useSkuWorkspaceContext,
  SkuOption,
} from '@/context/SkuWorkspaceContext';

export interface SkuSelectorProps {
  label?: string;
  availableSkus?: SkuOption[];
  className?: string;
}

export const SkuSelector: React.FC<SkuSelectorProps> = ({
  label = 'SKU',
  availableSkus,
  className = '',
}) => {
  const {
    selectedSkuId,
    setSelectedSkuId,
    availableSkus: globalSkus,
  } = useSkuWorkspaceContext();

  const options =
    availableSkus && availableSkus.length > 0
      ? availableSkus
      : globalSkus;

  const effectiveSku =
    options.some(
      (sku) => sku.id === selectedSkuId
    )
      ? selectedSkuId
      : options[0]?.id || '';

  const handleChange = (
    event: React.ChangeEvent<HTMLSelectElement>
  ) => {
    const nextSku = event.target.value;

    if (nextSku) {
      setSelectedSkuId(nextSku);
    }
  };

  return (
    <div
      className={`flex items-center gap-2.5 font-mono ${className}`}
    >
      <span className="text-[10px] text-slate-500 uppercase font-bold tracking-wider">
        {label}:
      </span>

      <select
        aria-label={`${label} selector`}
        value={effectiveSku}
        onChange={handleChange}
        className="bg-[#15171A] border border-white/15 rounded-lg px-3 py-1.5 text-white font-mono text-xs focus:outline-none focus:border-[#D4AF37] cursor-pointer min-w-[190px]"
      >
        {options.map((sku) => (
          <option
            key={sku.id}
            value={sku.id}
            className="bg-[#0C0E12] text-slate-200"
          >
            {sku.id} â€” {sku.name}
          </option>
        ))}
      </select>
    </div>
  );
};

export default SkuSelector;
