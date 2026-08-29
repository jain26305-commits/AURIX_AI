'use client';

import React from 'react';
import { AurixForecastBands } from './AurixForecastBands';
import { ForecastTimelinePoint } from '@/types/forecast.types';

export const AurixUncertaintyBand: React.FC<{ timeline: ForecastTimelinePoint[] }> = ({
  timeline,
}) => {
  return <AurixForecastBands timeline={timeline} height={260} />;
};