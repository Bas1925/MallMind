"use client";

import { toSvg, type Bounds, type RouteSegment, type VerticalHop } from "@/lib/map-geometry";

interface RouteLayerProps {
  bounds: Bounds;
  segments: RouteSegment[];
  hops: VerticalHop[];
}

const ROUTE = "#176b52";

export function RouteLayer({ bounds, segments, hops }: RouteLayerProps) {
  return (
    <g aria-label="Active route">
      {segments.map((segment, i) => {
        const d = segment.points
          .map((p, idx) => {
            const s = toSvg(p.x, p.y, bounds);
            return `${idx === 0 ? "M" : "L"} ${s.x} ${s.y}`;
          })
          .join(" ");
        return (
          <g key={`seg-${i}`} strokeLinecap="round" strokeLinejoin="round" fill="none">
            <path d={d} stroke="#ffffff" strokeWidth={3.2} />
            <path data-testid="route-path" d={d} stroke={ROUTE} strokeWidth={1.8} />
            <path d={d} stroke="#d2e8dc" strokeWidth={0.35} strokeDasharray="0.2 2.4" />
          </g>
        );
      })}
      {hops.map((hop, i) => {
        const p = toSvg(hop.x, hop.y, bounds);
        return (
          <g key={`hop-${i}`} transform={`translate(${p.x} ${p.y})`}>
            <circle r={3.1} fill="#ffffff" stroke={ROUTE} strokeWidth={0.7} />
            <text
              y={0.95}
              textAnchor="middle"
              fill={ROUTE}
              style={{ fontSize: 2.6, fontWeight: 700 }}
            >
              {hop.kind === "elevator" ? "E" : hop.kind === "stairs" ? "S" : "Es"}
            </text>
          </g>
        );
      })}
    </g>
  );
}
