"use client";

import { formatDuration } from "@/lib/map-geometry";
import type { RouteResponse } from "@/types/map";

interface RouteSummaryProps {
  route: RouteResponse;
  floorName: (level: number) => string;
}

function formatRouteMeters(meters: number): string {
  const rounded = Math.round(meters * 10) / 10;
  return Number.isInteger(rounded) ? `${rounded} m` : `${rounded.toFixed(1)} m`;
}

function tourLabel(algorithm: string): string | null {
  if (algorithm === "held_karp") return "Held-Karp";
  if (algorithm === "nearest_neighbor_2opt") return "nearest neighbor + 2-opt";
  if (algorithm === "user_order") return "the submitted order";
  return null;
}

export function RouteSummary({ route, floorName }: RouteSummaryProps) {
  const floors = route.floors.map((level) => floorName(level)).join(" → ");
  const tourAlgorithm = tourLabel(route.algorithm);
  return (
    <section data-testid="route-summary" className="rounded-xl border border-stone-200 bg-white p-4">
      <h2 className="text-sm font-semibold text-stone-900">
        {route.from_location} → {route.to_location}
      </h2>
      <dl className="mt-3 grid grid-cols-2 gap-x-3 gap-y-2 text-sm">
        <div>
          <dt className="text-xs text-stone-500">Distance</dt>
          <dd className="font-medium text-stone-900">{formatRouteMeters(route.distance_m)}</dd>
        </div>
        <div>
          <dt className="text-xs text-stone-500">Time</dt>
          <dd className="font-medium text-stone-900">{formatDuration(route.estimated_seconds)}</dd>
        </div>
        <div>
          <dt className="text-xs text-stone-500">Floors</dt>
          <dd className="font-medium text-stone-900">{floors}</dd>
        </div>
        <div>
          <dt className="text-xs text-stone-500">Profile</dt>
          <dd className="font-medium capitalize text-stone-900">{route.profile.replace("_", " ")}</dd>
        </div>
      </dl>
      <p className="mt-3 text-[11px] text-stone-400">
        {tourAlgorithm !== null
          ? `Tour ordered by ${tourAlgorithm} · ${route.nodes_expanded} A* pair calculations`
          : `Routed by ${route.algorithm.toUpperCase()} · ${route.nodes_expanded} nodes expanded`}
      </p>
    </section>
  );
}
