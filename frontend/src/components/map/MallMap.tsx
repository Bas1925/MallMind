"use client";

import { GraphDebugLayer } from "@/components/map/GraphDebugLayer";
import { LocationMarker } from "@/components/map/LocationMarker";
import { RouteLayer } from "@/components/map/RouteLayer";
import { SearchTrace } from "@/components/map/SearchTrace";
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
  traceLimit: number | null;
  perspective?: boolean;
  stops: Array<{ id: string; number: number }> | null;
  onSelectLocation: (id: string | null) => void;
}

export function MallMap({ payload, floorLevel, selectedId, startId, endId, route, showGraph, traceLimit, perspective = true, stops, onSelectLocation }: MallMapProps) {
  const floorNodes = payload.nodes.filter((node) => node.floor_level === floorLevel);
  const padded = boundsFor(floorNodes);
  // Keep room for store tiles while using more of the available map canvas.
  const bounds = { minX: padded.minX + 8, minY: padded.minY + 8, maxX: padded.maxX - 8, maxY: padded.maxY - 8 };
  const byId = new Map(payload.nodes.map((node) => [node.id, node]));
  const locations = payload.locations.filter((location) => location.floor_level === floorLevel);
  const routed = route === null ? { segments: [], hops: [] } : routeOnFloor(payload.nodes, payload.edges, route, floorLevel);
  const stopById = new Map((stops ?? []).map((stop) => [stop.id, stop.number]));
  const slab = floorRect(bounds);
  const seen = new Set<string>();
  const corridors = payload.edges.flatMap((edge) => {
    if (edge.edge_type !== "hallway" || edge.from_floor_level !== floorLevel || edge.to_floor_level !== floorLevel) return [];
    const pair = [edge.from_node_id, edge.to_node_id].sort().join(":");
    if (seen.has(pair)) return [];
    seen.add(pair);
    const a = byId.get(edge.from_node_id);
    const b = byId.get(edge.to_node_id);
    if (a === undefined || b === undefined) return [];
    return [{ id: edge.id, a: toSvg(a.x, a.y, bounds), b: toSvg(b.x, b.y, bounds) }];
  });

  return (
    <svg
      role="group"
      data-testid="mall-map"
      aria-label={`${payload.mall.name} floor map`}
      viewBox={viewBox(bounds)}
      preserveAspectRatio="xMidYMid meet"
      className="h-full w-full"
      onClick={() => onSelectLocation(null)}
    >
      <desc>Schematic wayfinding map. Store tiles indicate destinations, not surveyed shop boundaries. Select a location to plan your visit.</desc>
      <rect {...slab} rx={5} fill="#e8ebe3" stroke="#d7ded2" strokeWidth={0.3} />
      <rect x={slab.x + 1.2} y={slab.y + 1.2} width={slab.width - 2.4} height={slab.height - 2.4} rx={4} fill="none" stroke="#f6f7f3" strokeWidth={0.35} />

      {corridors.map((corridor) => (
        <line key={`border-${corridor.id}`} x1={corridor.a.x} y1={corridor.a.y} x2={corridor.b.x} y2={corridor.b.y} stroke="#dce1d7" strokeWidth={7.8} strokeLinecap="round" />
      ))}
      {corridors.map((corridor) => (
        <line key={corridor.id} x1={corridor.a.x} y1={corridor.a.y} x2={corridor.b.x} y2={corridor.b.y} stroke="#fffefa" strokeWidth={7} strokeLinecap="round" />
      ))}

      {showGraph ? (
        <GraphDebugLayer nodes={payload.nodes} edges={payload.edges} bounds={bounds} floorLevel={floorLevel} routeNodeIds={route === null ? [] : routeIds(route)} />
      ) : null}
      {route !== null && (route.algorithm === "bfs" || route.algorithm === "dfs") ? (
        <SearchTrace
          nodes={payload.nodes}
          bounds={bounds}
          floorLevel={floorLevel}
          visitedIds={(route.visited_ids ?? []).slice(0, traceLimit ?? undefined)}
          pathIds={routeIds(route)}
        />
      ) : null}
      <RouteLayer bounds={bounds} segments={routed.segments} hops={routed.hops} />
      {locations.map((location) => (
        <LocationMarker
          key={location.id}
          location={location}
          bounds={bounds}
          selected={location.id === selectedId}
          isStart={location.id === startId}
          isEnd={location.id === endId}
          stopNumber={stopById.get(location.id) ?? null}
          maxWidth={availableMarkerWidth(location, locations)}
          perspective={perspective}
          onSelect={onSelectLocation}
        />
      ))}
    </svg>
  );
}

/** Adjacent anchors share the available row space, keeping labels inside their tiles. */
function availableMarkerWidth(location: MapLocation, locations: MapLocation[]): number {
  if (location.x === null || location.y === null) return 18;
  let width = 18;
  for (const other of locations) {
    if (other.id === location.id || other.x === null || other.y === null) continue;
    if (Math.abs(other.y - location.y) < 14) {
      width = Math.min(width, Math.abs(other.x - location.x) - 2);
    }
  }
  return Math.max(8, width);
}
