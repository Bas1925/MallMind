"use client";

import { toSvg, type Bounds, type RouteSegment, type VerticalHop } from "@/lib/map-geometry";

interface RouteLayerProps {
  bounds: Bounds;
  segments: RouteSegment[];
  hops: VerticalHop[];
}

const GOLD = "#f2cf8a";

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
            <path d={d} stroke={GOLD} strokeWidth={4.5} opacity={0.35} filter="url(#soft-glow)" />
            <path data-testid="route-path" d={d} stroke={GOLD} strokeWidth={1.9} />
            <path d={d} stroke="#fff8e8" strokeWidth={0.7} opacity={0.85} className="route-flow" />
          </g>
        );
      })}
      {hops.map((hop, i) => {
        const p = toSvg(hop.x, hop.y, bounds);
        return (
          <g key={`hop-${i}`} transform={`translate(${p.x} ${p.y})`}>
            <circle r={3.1} fill="#0b0e14" stroke={GOLD} strokeWidth={0.8} />
            <text
              y={0.95}
              textAnchor="middle"
              fill={GOLD}
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
