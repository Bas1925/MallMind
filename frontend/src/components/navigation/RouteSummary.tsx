"use client";

import { Icon } from "@/components/ui/Icon";
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
  const tourAlgorithm = tourLabel(route.algorithm);
  const [distance, unit] = formatRouteMeters(route.distance_m).split(" ");
  return (
    <section
      data-testid="route-summary"
      className="rise relative overflow-hidden rounded-2xl border border-gold-400/20 bg-gradient-to-br from-gold-400/[0.10] via-white/[0.02] to-transparent p-4"
    >
      <div className="flex items-center justify-between">
        <p className="eyebrow">Your route</p>
        {route.profile !== "normal" ? (
          <span className="rounded-full bg-gold-400/15 px-2 py-0.5 text-[11px] font-medium capitalize text-gold-200">
            {route.profile.replace("_", " ")}
          </span>
        ) : null}
      </div>
      <h2 className="mt-1 text-sm font-semibold text-mist-50">
        {route.from_location} <span className="text-gold-300">→</span> {route.to_location}
      </h2>

      <dl className="mt-4 grid grid-cols-2 gap-3">
        <div>
          <dt className="flex items-center gap-1.5 text-[11px] text-mist-500">
            <Icon name="ruler" size={12} /> Distance
          </dt>
          <dd className="font-display text-4xl leading-none text-mist-50">
            {distance}{" "}
            <span className="font-sans text-sm text-mist-400">{unit}</span>
          </dd>
        </div>
        <div>
          <dt className="flex items-center gap-1.5 text-[11px] text-mist-500">
            <Icon name="clock" size={12} /> Time
          </dt>
          <dd className="font-display text-4xl leading-none text-mist-50">
            {formatDuration(route.estimated_seconds).replace(" min", "")}{" "}
            <span className="font-sans text-sm text-mist-400">min</span>
          </dd>
        </div>
      </dl>

      <div className="mt-4 flex flex-wrap items-center gap-1.5">
        <span className="sr-only">Floors</span>
        {route.floors.map((level, i) => (
          <span key={`${level}-${i}`} className="flex items-center gap-1.5">
            {i > 0 ? <span className="text-mist-500">→</span> : null}
            <span className="rounded-full border border-white/[0.08] bg-ink-900/60 px-2 py-0.5 text-[11px] font-medium text-mist-200">
              {floorName(level)}
            </span>
          </span>
        ))}
      </div>

      <p className="mt-4 border-t border-white/[0.06] pt-3 font-mono text-[10px] tracking-tight text-mist-500">
        {tourAlgorithm !== null
          ? `Tour ordered by ${tourAlgorithm} · ${route.nodes_expanded} A* pair calculations`
          : `Routed by ${route.algorithm.toUpperCase()} · ${route.nodes_expanded} nodes expanded`}
      </p>
    </section>
  );
}
