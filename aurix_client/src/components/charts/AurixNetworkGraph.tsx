'use client';

import React from 'react';
import { TopologyCanvas } from '@/components/features/network/TopologyCanvas';
import { NetworkTopologyNode, NetworkTopologyEdge } from '@/types/network.types';

export const AurixNetworkGraph: React.FC<{
  nodes: NetworkTopologyNode[];
  edges: NetworkTopologyEdge[];
  selectedNodeId: string | null;
  onSelectNode: (id: string) => void;
}> = (props) => {
  return <TopologyCanvas {...props} />;
};