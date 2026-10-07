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

  return (
    <svg
      role="img"
      data-testid="mall-map"
      aria-label={`${payload.mall.name} floor map`}
      viewBox={viewBox(bounds)}
      className="h-full w-full bg-[#f4f1ea]"
      onClick={() => onSelectLocation(null)}
    >
      <rect
        {...floorRect(bounds)}
        rx={4}
        fill="#efeae0"
        stroke="#d6d0c4"
        strokeWidth={0.6}
      />
      {hallway.map((edge) => {
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
            stroke="#ddd6c8"
            strokeWidth={5.5}
            strokeLinecap="round"
          />
        );
      })}
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
      <EndpointHalo
        location={startLoc}
        bounds={bounds}
        color="#15803d"
        label="Start"
        floorLevel={floorLevel}
      />
      <EndpointHalo
        location={endLoc}
        bounds={bounds}
        color="#c2410c"
        label="End"
        floorLevel={floorLevel}
      />
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
      <circle r={4.2} fill="none" stroke={color} strokeWidth={0.7} opacity={0.85} />
      <text y={6.2} textAnchor="middle" style={{ fontSize: 2.4, fontWeight: 700 }} fill={color}>
        {label}
      </text>
    </g>
  );
}
