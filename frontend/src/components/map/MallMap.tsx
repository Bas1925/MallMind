"use client";

import { GraphDebugLayer } from "@/components/map/GraphDebugLayer";
import { LocationMarker } from "@/components/map/LocationMarker";
import { RouteLayer } from "@/components/map/RouteLayer";
import { boundsFor, floorRect, routeIds, routeOnFloor, toSvg, viewBox } from "@/lib/map-geometry";
import type { MallMapPayload, MapLocation, RouteResponse } from "@/types/map";

interface MallMapProps {
  payload: MallMapPayload;
  floorLevel: number;
  selectedId: string | null;
  startId: string | null;
  endId: string | null;
  route: RouteResponse | null;
  showGraph: boolean;
  stops: Array<{ id: string; number: number }> | null;
  onSelectLocation: (id: string | null) => void;
}

const START = "#3ddc97";
const END = "#ff6b81";

export function MallMap({
  payload,
  floorLevel,
  selectedId,
  startId,
  endId,
  route,
  showGraph,
  stops,
  onSelectLocation,
}: MallMapProps) {
  const floorNodes = payload.nodes.filter((n) => n.floor_level === floorLevel);
  const bounds = boundsFor(floorNodes);
  const hallway = payload.edges.filter(
    (e) =>
      e.edge_type === "hallway" &&
      e.from_floor_level === floorLevel &&
      e.to_floor_level === floorLevel,
  );
  const byId = new Map(payload.nodes.map((n) => [n.id, n]));
  const locations = payload.locations.filter((loc) => loc.floor_level === floorLevel);
  const routed = route === null ? { segments: [], hops: [] } : routeOnFloor(payload.nodes, payload.edges, route, floorLevel);
  const startLoc = payload.locations.find((l) => l.id === startId);
  const endLoc = payload.locations.find((l) => l.id === endId);
  const stopById = new Map((stops ?? []).map((stop) => [stop.id, stop.number]));
  const slab = floorRect(bounds);

  const corridors = hallway.flatMap((edge) => {
    const a = byId.get(edge.from_node_id);
    const b = byId.get(edge.to_node_id);
    if (a === undefined || b === undefined) return [];
    return [{ id: edge.id, a: toSvg(a.x, a.y, bounds), b: toSvg(b.x, b.y, bounds) }];
  });

  return (
    <svg
      role="img"
      data-testid="mall-map"
      aria-label={`${payload.mall.name} floor map`}
      viewBox={viewBox(bounds)}
      className="h-full w-full"
      onClick={() => onSelectLocation(null)}
    >
      <defs>
        <pattern id="floor-dots" width={4} height={4} patternUnits="userSpaceOnUse">
          <circle cx={0.5} cy={0.5} r={0.18} fill="#ffffff" opacity={0.07} />
        </pattern>
        <linearGradient id="slab-fill" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" stopColor="#151a23" />
          <stop offset="1" stopColor="#10141c" />
        </linearGradient>
        <filter id="soft-glow" x="-50%" y="-50%" width="200%" height="200%">
          <feGaussianBlur stdDeviation={1.4} />
        </filter>
      </defs>

      <rect {...slab} rx={5} fill="url(#slab-fill)" stroke="#2a3240" strokeWidth={0.35} />
      <rect {...slab} rx={5} fill="url(#floor-dots)" />

      {/* Corridors: a dark bed, then a lighter walkway, so junctions read as one surface. */}
      {corridors.map((c) => (
        <line
          key={`bed-${c.id}`}
          x1={c.a.x}
          y1={c.a.y}
          x2={c.b.x}
          y2={c.b.y}
          stroke="#0b0e14"
          strokeWidth={7}
          strokeLinecap="round"
        />
      ))}
      {corridors.map((c) => (
        <line
          key={c.id}
          x1={c.a.x}
          y1={c.a.y}
          x2={c.b.x}
          y2={c.b.y}
          stroke="#212834"
          strokeWidth={5}
          strokeLinecap="round"
        />
      ))}

      {showGraph ? (
        <GraphDebugLayer
          nodes={payload.nodes}
          edges={payload.edges}
          bounds={bounds}
          floorLevel={floorLevel}
          routeNodeIds={route === null ? [] : routeIds(route)}
        />
      ) : null}
      <RouteLayer bounds={bounds} segments={routed.segments} hops={routed.hops} />
      <EndpointHalo location={startLoc} bounds={bounds} color={START} label="Start" floorLevel={floorLevel} />
      <EndpointHalo location={endLoc} bounds={bounds} color={END} label="End" floorLevel={floorLevel} />
      {locations.map((loc) => (
        <LocationMarker
          key={loc.id}
          location={loc}
          bounds={bounds}
          selected={loc.id === selectedId}
          isStart={loc.id === startId}
          isEnd={loc.id === endId}
          stopNumber={stopById.get(loc.id) ?? null}
          onSelect={(id) => onSelectLocation(id)}
        />
      ))}
    </svg>
  );
}

function EndpointHalo({
  location,
  bounds,
  color,
  label,
  floorLevel,
}: {
  location: MapLocation | undefined;
  bounds: ReturnType<typeof boundsFor>;
  color: string;
  label: string;
  floorLevel: number;
}) {
  if (location === undefined || location.x === null || location.y === null) return null;
  if (location.floor_level !== floorLevel) return null;
  const p = toSvg(location.x, location.y, bounds);
  return (
    <g transform={`translate(${p.x} ${p.y})`} pointerEvents="none">
      <circle r={3.4} fill="none" stroke={color} strokeWidth={0.5} className="pulse-ring" />
      <circle r={3.4} fill="none" stroke={color} strokeWidth={0.6} opacity={0.9} />
      <g transform="translate(0 6.4)">
        <rect x={-4.6} y={-1.7} width={9.2} height={3.4} rx={1.7} fill={color} />
        <text
          y={0.75}
          textAnchor="middle"
          fill="#07090d"
          style={{ fontSize: 2, fontWeight: 700, letterSpacing: 0.15 }}
        >
          {label.toUpperCase()}
        </text>
      </g>
    </g>
  );
}
