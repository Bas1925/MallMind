"use client";

import { toSvg, type Bounds, type RouteSegment, type VerticalHop } from "@/lib/map-geometry";

interface RouteLayerProps {
  bounds: Bounds;
  segments: RouteSegment[];
  hops: VerticalHop[];
}

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
          <path
            key={`seg-${i}`}
            data-testid="route-path"
            d={d}
            fill="none"
            stroke="#c2410c"
            strokeWidth={2.4}
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        );
      })}
      {hops.map((hop, i) => {
        const p = toSvg(hop.x, hop.y, bounds);
        return (
          <g key={`hop-${i}`} transform={`translate(${p.x} ${p.y})`}>
            <circle r={3.2} fill="#fff" stroke="#c2410c" strokeWidth={1.2} />
            <text
              y={-4.5}
              textAnchor="middle"
              className="fill-orange-700"
              style={{ fontSize: 3.2, fontWeight: 600 }}
            >
              {hop.kind === "elevator" ? "E" : hop.kind === "stairs" ? "S" : "Esc"}
            </text>
          </g>
        );
      })}
    </g>
  );
}
