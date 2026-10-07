"use client";

import { toSvg, type Bounds } from "@/lib/map-geometry";
import type { MapEdge, MapNode } from "@/types/map";

interface GraphDebugLayerProps {
  nodes: MapNode[];
  edges: MapEdge[];
  bounds: Bounds;
  floorLevel: number;
  routeNodeIds: string[];
}

export function GraphDebugLayer({
  nodes,
  edges,
  bounds,
  floorLevel,
  routeNodeIds,
}: GraphDebugLayerProps) {
  const onFloor = nodes.filter((n) => n.floor_level === floorLevel);
  const byId = new Map(onFloor.map((n) => [n.id, n]));
  const routeSet = new Set(routeNodeIds);

  return (
    <g aria-hidden>
      {edges.map((edge) => {
        if (edge.from_floor_level !== floorLevel || edge.to_floor_level !== floorLevel) return null;
        const a = byId.get(edge.from_node_id);
        const b = byId.get(edge.to_node_id);
        if (a === undefined || b === undefined) return null;
        const pa = toSvg(a.x, a.y, bounds);
        const pb = toSvg(b.x, b.y, bounds);
        return (
          <line
            key={edge.id}
            x1={pa.x}
            y1={pa.y}
            x2={pb.x}
            y2={pb.y}
            stroke="#5ec8ff"
            strokeWidth={0.3}
            opacity={0.45}
          />
        );
      })}
      {onFloor.map((node) => {
        const p = toSvg(node.x, node.y, bounds);
        const onRoute = routeSet.has(node.id);
        return (
          <g key={node.id} transform={`translate(${p.x} ${p.y})`}>
            <circle r={0.9} fill={onRoute ? "#f2cf8a" : "#5ec8ff"} />
            <text y={1.8} textAnchor="middle" style={{ fontSize: 1.6 }} fill="#7b818c">
              {node.id.slice(0, 4)}
            </text>
          </g>
        );
      })}
    </g>
  );
}
