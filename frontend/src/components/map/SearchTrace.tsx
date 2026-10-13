"use client";

import { toSvg, type Bounds } from "@/lib/map-geometry";
import type { MapNode } from "@/types/map";

interface SearchTraceProps {
  nodes: MapNode[];
  bounds: Bounds;
  floorLevel: number;
  visitedIds: string[];
  pathIds: string[];
}

/** Numbers are the order the search checked each place. */
export function SearchTrace({ nodes, bounds, floorLevel, visitedIds, pathIds }: SearchTraceProps) {
  const byId = new Map(nodes.map((node) => [node.id, node]));
  const onPath = new Set(pathIds);
  const marks = visitedIds.flatMap((id, index) => {
    const node = byId.get(id);
    if (node === undefined || node.floor_level !== floorLevel) return [];
    return [{ id, index, point: toSvg(node.x, node.y, bounds), onPath: onPath.has(id) }];
  });

  return (
    <g aria-label="Search order">
      {marks.map((mark) => (
        <g key={mark.id} transform={`translate(${mark.point.x} ${mark.point.y})`}>
          <title>{`Checked ${mark.index + 1}${mark.onPath ? ", on the path" : ""}`}</title>
          <circle r={2.4} fill={mark.onPath ? "#176b52" : "#fff"} stroke="#176b52" strokeWidth={0.45} />
          <text y={0.85} textAnchor="middle" fill={mark.onPath ? "#fff" : "#176b52"} style={{ fontSize: 2.15, fontWeight: 700 }}>
            {mark.index + 1}
          </text>
        </g>
      ))}
    </g>
  );
}
