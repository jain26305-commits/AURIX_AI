'use client';

import React from 'react';
import { NetworkTopologyNode, NetworkTopologyEdge } from '@/types/network.types';
import { Share2 } from 'lucide-react';


interface TopologyCanvasProps {
  nodes: NetworkTopologyNode[];
  edges: NetworkTopologyEdge[];
  selectedNodeId: string | null;
  onSelectNode: (id: string) => void;
}

export const TopologyCanvas: React.FC<TopologyCanvasProps> = ({
  nodes,
  edges,
  selectedNodeId,
  onSelectNode,
}) => {
  const width = 1080;
  const height = 240;

  return (
    <div className="w-full aurix-card-glass rounded-xl p-6 border border-white/[0.08] select-none">
      <div className="flex items-center justify-between pb-4 mb-4 border-b border-white/[0.06]">
        <div>
          <h3 className="text-sm font-semibold text-white tracking-wide flex items-center gap-2">
            <Share2 className="w-4 h-4 text-[#D4AF37]" />
            MULTI-ECHELON TOPOLOGICAL GRAPH & BOTTLENECK ROUTING
          </h3>
          <p className="text-[11px] font-mono text-slate-400 mt-0.5">
            End-to-end supply flow with bottleneck indicator and node capacity utilization.
          </p>
        </div>
      </div>

      <div className="relative w-full overflow-x-auto">
        <svg viewBox={`0 0 ${width} ${height}`} className="w-full min-w-[900px] h-auto overflow-visible">
          <defs>
            <linearGradient id="edgeNormal" x1="0" y1="0" x2="1" y2="0">
              <stop offset="0%" stopColor="#D4AF37" stopOpacity="0.6" />
              <stop offset="100%" stopColor="#D4AF37" stopOpacity="0.2" />
            </linearGradient>
            <linearGradient id="edgeBottleneck" x1="0" y1="0" x2="1" y2="0">
              <stop offset="0%" stopColor="#FF6B6B" stopOpacity="0.8" />
              <stop offset="100%" stopColor="#FF6B6B" stopOpacity="0.3" />
            </linearGradient>
          </defs>

          {/* Render Flow Edges */}
          {edges.map((edge) => {
            const source = nodes.find((n) => n.id === edge.sourceNodeId);
            const target = nodes.find((n) => n.id === edge.targetNodeId);
            if (!source || !target) return null;

            return (
              <g key={edge.id}>
                <line
                  x1={source.x}
                  y1={source.y}
                  x2={target.x}
                  y2={target.y}
                  stroke={edge.isBottleneck ? 'url(#edgeBottleneck)' : 'url(#edgeNormal)'}
                  strokeWidth={edge.isBottleneck ? 3 : 1.8}
                  strokeDasharray={edge.isBottleneck ? '4 4' : undefined}
                />
                {/* Edge Metric Label */}
                <text
                  x={(source.x + target.x) / 2}
                  y={(source.y + target.y) / 2 - 8}
                  textAnchor="middle"
                  className={`text-[8px] font-mono font-bold ${
                    edge.isBottleneck ? 'fill-[#FF8585]' : 'fill-slate-500'
                  }`}
                >
                  {edge.leadTimeDays}d lead ({edge.flowVolumeUnitsPerMonth}u/mo)
                </text>
              </g>
            );
          })}

          {/* Render Nodes */}
          {nodes.map((node) => {
            const isSelected = node.id === selectedNodeId;
            const isCongested = node.status === 'CONGESTED';

            return (
              <g
                key={node.id}
                onClick={() => onSelectNode(node.id)}
                className="cursor-pointer transition-transform duration-200"
              >
                {/* Node Outer Glow Ring */}
                <circle
                  cx={node.x}
                  cy={node.y}
                  r={isSelected ? 26 : 20}
                  fill={isCongested ? 'rgba(255,107,107,0.15)' : 'rgba(212,175,55,0.1)'}
                  stroke={isSelected ? '#D4AF37' : isCongested ? '#FF6B6B' : '#D4AF37'}
                  strokeWidth={isSelected ? 2.5 : 1.5}
                />

                <circle cx={node.x} cy={node.y} r={6} fill={isCongested ? '#FF6B6B' : '#D4AF37'} />

                {/* Node Labels */}
                <text
                  x={node.x}
                  y={node.y + 34}
                  textAnchor="middle"
                  className={`text-[9px] font-mono font-bold ${
                    isSelected ? 'fill-gold' : 'fill-white'
                  }`}
                >
                  {node.name.length > 22 ? node.name.substring(0, 20) + '...' : node.name}
                </text>
                <text
                  x={node.x}
                  y={node.y + 45}
                  textAnchor="middle"
                  className="text-[8px] font-mono fill-slate-500"
                >
                  {node.tier} • {node.capacityUtilizationPercent}% cap
                </text>
              </g>
            );
          })}
        </svg>
      </div>
    </div>
  );
};