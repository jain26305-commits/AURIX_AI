'use client';

import React, { useState } from 'react';
import { NetworkTopologyNode, NetworkTopologyEdge, DisruptionPropagationPath } from '@/types/network.types';
import { AurixCard } from '@/components/ui/AurixCard';
import { AurixBadge } from '@/components/ui/AurixBadge';
import { AurixButton } from '@/components/ui/AurixButton';
import { ShieldAlert, Zap } from 'lucide-react';

interface NetworkTopologyGraphProps {
  nodes: NetworkTopologyNode[];
  edges: NetworkTopologyEdge[];
  simulatedPropagation?: DisruptionPropagationPath;
}

export const NetworkTopologyGraph: React.FC<NetworkTopologyGraphProps> = ({
  nodes,
  edges,
  simulatedPropagation,
}) => {
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);
  const [showPropagation, setShowPropagation] = useState<boolean>(false);

  const selectedNode = nodes.find((n) => n.id === selectedNodeId);

  const getNodeColor = (status: NetworkTopologyNode['status']) => {
    switch (status) {
      case 'DISRUPTED':
        return '#FF6B6B';
      case 'CONGESTED':
        return '#F3B33D';
      case 'HEALTHY':
      default:
        return '#3DDB91';
    }
  };

  return (
    <div className="space-y-6">
      <AurixCard
        title="DIRECTED MULTI-ECHELON TOPOLOGY GRAPH"
        subtitle="Physical facility node telemetry, bottleneck transportation links, and flow capacities"
        badge={
          <div className="flex items-center gap-2">
            {simulatedPropagation && (
              <AurixButton
                variant={showPropagation ? 'gold' : 'secondary'}
                size="sm"
                onClick={() => setShowPropagation(!showPropagation)}
              >
                <Zap className="w-3.5 h-3.5 mr-1" />
                {showPropagation ? 'HIDE PROPAGATION TRACE' : 'TRACE DISRUPTION PATH'}
              </AurixButton>
            )}
            <AurixBadge variant="gold">{nodes.length} ACTIVE NODES</AurixBadge>
          </div>
        }
      >
        <div className="space-y-4 font-mono text-xs">
          {/* SVG Canvas */}
          <div className="w-full h-80 rounded-xl bg-black/40 border border-white/[0.06] relative overflow-hidden flex items-center justify-center p-4">
            <svg className="w-full h-full" viewBox="0 0 1100 240" fill="none">
              {/* Edges */}
              {edges.map((edge) => {
                const source = nodes.find((n) => n.id === edge.sourceNodeId);
                const target = nodes.find((n) => n.id === edge.targetNodeId);
                if (!source || !target) return null;

                const isPropagationEdge =
                  showPropagation &&
                  (simulatedPropagation?.propagation_path.some(
                    (p) => p.entity_id === target.id
                  ) ?? false);

                return (
                  <g key={edge.id}>
                    <line
                      x1={source.x}
                      y1={source.y}
                      x2={target.x}
                      y2={target.y}
                      stroke={
                        isPropagationEdge
                          ? '#FF6B6B'
                          : edge.isBottleneck
                          ? '#FF6B6B'
                          : 'rgba(255,255,255,0.15)'
                      }
                      strokeWidth={edge.isBottleneck || isPropagationEdge ? 2.5 : 1.5}
                      strokeDasharray={edge.isBottleneck ? '4 3' : isPropagationEdge ? '2 2' : undefined}
                    />
                  </g>
                );
              })}

              {/* Nodes */}
              {nodes.map((node) => {
                const isSelected = node.id === selectedNodeId;
                const isRootRisk =
                  showPropagation && simulatedPropagation?.root_risk_entity === node.id;
                const isDownstreamImpact =
                  showPropagation &&
                  (simulatedPropagation?.propagation_path.some((p) => p.entity_id === node.id) ?? false);

                return (
                  <g
                    key={node.id}
                    className="cursor-pointer transition-transform hover:scale-105"
                    onClick={() => setSelectedNodeId(node.id)}
                  >
                    <circle
                      cx={node.x}
                      cy={node.y}
                      r={isRootRisk ? 16 : isSelected ? 14 : 10}
                      fill={
                        isRootRisk
                          ? '#FF6B6B'
                          : isDownstreamImpact
                          ? '#F3B33D'
                          : getNodeColor(node.status)
                      }
                      fillOpacity={0.25}
                      stroke={
                        isRootRisk
                          ? '#FF6B6B'
                          : isDownstreamImpact
                          ? '#F3B33D'
                          : getNodeColor(node.status)
                      }
                      strokeWidth={isSelected || isRootRisk ? 2.5 : 1.5}
                    />
                    <circle
                      cx={node.x}
                      cy={node.y}
                      r={4}
                      fill={
                        isRootRisk
                          ? '#FF6B6B'
                          : isDownstreamImpact
                          ? '#F3B33D'
                          : getNodeColor(node.status)
                      }
                    />
                    <text
                      x={node.x}
                      y={node.y + 24}
                      textAnchor="middle"
                      fill="#CBD5E1"
                      fontSize="9"
                      fontFamily="monospace"
                    >
                      {node.id}
                    </text>
                  </g>
                );
              })}
            </svg>
          </div>

          {/* Node Metadata Strip */}
          {selectedNode && (
            <div className="p-4 rounded-xl bg-white/[0.02] border border-white/[0.06] grid grid-cols-2 md:grid-cols-4 gap-4 animate-pure-fade">
              <div>
                <span className="text-[10px] text-slate-500 uppercase block">NODE IDENTITY</span>
                <span className="text-white font-bold block truncate">{selectedNode.name}</span>
                <span className="text-[10px] text-slate-400">{selectedNode.tier} • {selectedNode.location}</span>
              </div>

              <div>
                <span className="text-[10px] text-slate-500 uppercase block">UTILIZATION</span>
                <span className="text-white font-bold block">{selectedNode.capacityUtilizationPercent}%</span>
                <span className="text-[10px] text-slate-400">{selectedNode.throughputPerDay} units/day</span>
              </div>

              <div>
                <span className="text-[10px] text-slate-500 uppercase block">HOLDING CAPITAL</span>
                <span className="text-white font-bold block">₹{(selectedNode.holdingValueINR / 100000).toFixed(2)}L</span>
                <span className="text-[10px] text-slate-400">Locked Inventory</span>
              </div>

              <div>
                <span className="text-[10px] text-slate-500 uppercase block">VULNERABILITY INDEX</span>
                <span className="text-[#D4AF37] font-bold block">{selectedNode.vulnerabilityScore} / 100</span>
                <span className="text-[10px] text-slate-400">Failure Risk</span>
              </div>
            </div>
          )}
        </div>
      </AurixCard>

      {/* Disruption Propagation Drawer / Card */}
      {showPropagation && simulatedPropagation && (
        <AurixCard
          title="CROSS-ECHELON DISRUPTION PROPAGATION SOLVER"
          subtitle={"Downstream operational shockwaves starting from root disruption: " + simulatedPropagation.root_risk_entity}
          badge={<AurixBadge variant="danger">{simulatedPropagation.total_downstream_entities_affected} HOPS AFFECTED</AurixBadge>}
        >
          <div className="space-y-4 pt-2 font-mono text-xs">
            <div className="flex items-center justify-between p-3 rounded-lg bg-[#FF6B6B]/10 border border-[#FF6B6B]/30">
              <div className="flex items-center gap-2">
                <ShieldAlert className="w-4 h-4 text-[#FF8585]" />
                <span className="text-white font-bold">TOTAL REVENUE EXPOSED DOWNSTREAM</span>
              </div>
              <span className="text-[#FF8585] text-sm font-bold">
                ${simulatedPropagation.total_revenue_exposed_usd.toLocaleString()}
              </span>
            </div>

            <div className="space-y-2">
              <span className="text-[10px] text-slate-400 uppercase tracking-widest block">
                TRAVERSED PROPAGATION PATHWAYS (CYCLE-SAFE HOP ENGINE)
              </span>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {simulatedPropagation.propagation_path.map((path) => (
                  <div
                    key={path.entity_id}
                    className="p-3 rounded-lg bg-white/[0.02] border border-white/[0.06] flex items-center justify-between"
                  >
                    <div>
                      <div className="flex items-center gap-2">
                        <AurixBadge variant="neutral" size="sm">HOP {path.hop}</AurixBadge>
                        <span className="text-white font-bold truncate">{path.entity_name}</span>
                      </div>
                      <span className="text-[10px] text-slate-500 block mt-1">
                        ID: {path.entity_id} • Type: {path.entity_type}
                      </span>
                    </div>

                    <div className="text-right">
                      <span className="text-[10px] text-slate-500 block uppercase">EXPOSURE</span>
                      <span className="text-[#FF8585] font-bold">${path.financial_exposure_usd.toLocaleString()}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </AurixCard>
      )}
    </div>
  );
};
