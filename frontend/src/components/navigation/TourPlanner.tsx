"use client";

import { useMemo, useState } from "react";
import { optimizeTour } from "@/lib/api";
import { formatDuration } from "@/lib/map-geometry";
import type { MapLocation, RouteProfile } from "@/types/map";
import type { OptimizeResponse } from "@/types/tour";

interface TourPlannerProps {
  locations: MapLocation[];
  profile: RouteProfile;
  onProfile: (profile: RouteProfile) => void;
  onApply: (plan: OptimizeResponse) => void;
}

const PROFILES: Array<{ id: RouteProfile; label: string }> = [
  { id: "normal", label: "Standard" },
  { id: "wheelchair", label: "Wheelchair" },
  { id: "avoid_stairs", label: "Avoid stairs" },
];

export function TourPlanner({ locations, profile, onProfile, onApply }: TourPlannerProps) {
  const entrance = locations.find((loc) => loc.slug === "main-entrance");
  const [startId, setStartId] = useState(entrance?.id ?? locations[0]?.id ?? "");
  const [stopIds, setStopIds] = useState<string[]>([]);
  const [query, setQuery] = useState("");
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [plan, setPlan] = useState<OptimizeResponse | null>(null);
  const [details, setDetails] = useState(false);

  const byId = useMemo(() => new Map(locations.map((loc) => [loc.id, loc])), [locations]);
  const choices = locations.filter((loc) => {
    if (loc.id === startId || stopIds.includes(loc.id)) return false;
    const q = query.trim().toLowerCase();
    if (q === "") return true;
    return loc.name.toLowerCase().includes(q) || loc.category_name.toLowerCase().includes(q);
  });

  async function optimize(): Promise<void> {
    if (startId === "" || stopIds.length === 0) return;
    setPending(true);
    setError(null);
    try {
      const result = await optimizeTour({
        startLocationId: startId,
        locationIds: stopIds,
        profile,
      });
      setPlan(result);
      onApply(result);
    } catch (err) {
      setPlan(null);
      setError(err instanceof Error ? err.message : "Could not optimize the route");
    } finally {
      setPending(false);
    }
  }

  function move(index: number, delta: number): void {
    const next = index + delta;
    if (next < 0 || next >= stopIds.length) return;
    const copy = [...stopIds];
    const current = copy[index];
    const swap = copy[next];
    if (current === undefined || swap === undefined) return;
    copy[index] = swap;
    copy[next] = current;
    setStopIds(copy);
  }

  return (
    <section className="space-y-3" data-testid="tour-planner">
      <label className="flex flex-col gap-1 text-xs font-medium text-stone-600">
        Start
        <select
          data-testid="tour-start"
          value={startId}
          onChange={(event) => {
            setStartId(event.target.value);
            setStopIds((ids) => ids.filter((id) => id !== event.target.value));
          }}
          className="rounded-lg border border-stone-200 bg-white px-3 py-2 text-sm text-stone-900"
        >
          {locations.map((loc) => (
            <option key={loc.id} value={loc.id}>
              {loc.name} · {loc.floor_name}
            </option>
          ))}
        </select>
      </label>

      <div className="flex flex-col gap-1 text-xs font-medium text-stone-600">
        Stops
        <input
          data-testid="tour-search"
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          placeholder="Add Nike, an ATM, a pharmacy…"
          className="rounded-lg border border-stone-200 px-3 py-2 text-sm text-stone-900"
        />
        {query.trim() !== "" && choices.length > 0 ? (
          <ul className="max-h-32 overflow-auto rounded-lg border border-stone-200 bg-white">
            {choices.slice(0, 6).map((loc) => (
              <li key={loc.id}>
                <button
                  type="button"
                  className="flex w-full flex-col items-start px-3 py-1.5 text-start hover:bg-stone-50"
                  onClick={() => {
                    setStopIds((ids) => [...ids, loc.id]);
                    setQuery("");
                  }}
                >
                  <span className="text-sm text-stone-900">{loc.name}</span>
                  <span className="text-[11px] text-stone-500">
                    {loc.category_name} · {loc.floor_name}
                  </span>
                </button>
              </li>
            ))}
          </ul>
        ) : null}
      </div>

      {stopIds.length > 0 ? (
        <ol data-testid="tour-stops" className="space-y-1">
          {stopIds.map((id, index) => {
            const loc = byId.get(id);
            return (
              <li key={id} className="flex items-center gap-2 text-sm">
                <span className="w-4 text-xs text-stone-400">{index + 1}</span>
                <span className="min-w-0 flex-1 truncate">{loc?.name ?? id}</span>
                <button type="button" className="text-xs text-stone-500" onClick={() => move(index, -1)}>
                  Up
                </button>
                <button type="button" className="text-xs text-stone-500" onClick={() => move(index, 1)}>
                  Down
                </button>
                <button
                  type="button"
                  className="text-xs text-stone-500"
                  onClick={() => setStopIds((ids) => ids.filter((item) => item !== id))}
                >
                  Remove
                </button>
              </li>
            );
          })}
        </ol>
      ) : (
        <p className="text-xs text-stone-500">Add the stores you want to visit. Order is the baseline.</p>
      )}

      <fieldset className="flex flex-wrap gap-2">
        {PROFILES.map((item) => (
          <label key={item.id} className="flex items-center gap-1 text-xs text-stone-700">
            <input
              type="radio"
              name="tour-profile"
              value={item.id}
              checked={profile === item.id}
              onChange={() => onProfile(item.id)}
            />
            {item.label}
          </label>
        ))}
      </fieldset>

      <button
        type="button"
        data-testid="tour-optimize"
        disabled={pending || startId === "" || stopIds.length === 0}
        onClick={() => void optimize()}
        className="w-full rounded-lg bg-stone-900 px-3 py-2 text-sm font-semibold text-white disabled:opacity-40"
      >
        {pending ? "Optimizing…" : "Optimize route"}
      </button>

      {error !== null ? (
        <p data-testid="tour-error" className="text-sm text-red-800">
          {error}
        </p>
      ) : null}

      {plan !== null ? (
        <TourResult
          plan={plan}
          details={details}
          onToggle={() => setDetails((open) => !open)}
          onStart={() => onApply(plan)}
        />
      ) : null}
    </section>
  );
}

function TourResult({
  plan,
  details,
  onToggle,
  onStart,
}: {
  plan: OptimizeResponse;
  details: boolean;
  onToggle: () => void;
  onStart: () => void;
}) {
  return (
    <div className="space-y-2" data-testid="tour-result">
      <p className="text-sm font-semibold text-stone-900">
        {plan.optimized_order.length - 1} stops
      </p>
      <div className="grid grid-cols-2 gap-2 text-sm">
        <div className="rounded-lg bg-stone-50 px-3 py-2">
          <p className="text-[11px] uppercase tracking-wide text-stone-500">Original</p>
          <p>{formatMeters(plan.original_distance_m)}</p>
          <p className="text-stone-500">{formatDuration(plan.original_seconds)}</p>
        </div>
        <div className="rounded-lg bg-orange-50 px-3 py-2">
          <p className="text-[11px] uppercase tracking-wide text-orange-800">Optimized</p>
          <p>{formatMeters(plan.optimized_distance_m)}</p>
          <p className="text-stone-500">{formatDuration(plan.optimized_seconds)}</p>
        </div>
      </div>
      {plan.improved ? (
        <p data-testid="tour-savings" className="text-sm font-medium text-stone-900">
          You save {formatMeters(plan.distance_saved_m)}
          {plan.distance_saved_percent !== null ? ` · ${plan.distance_saved_percent}%` : ""}
          {plan.estimated_time_saved_seconds > 0
            ? ` · ${formatSavedTime(plan.estimated_time_saved_seconds)}`
            : ""}
        </p>
      ) : (
        <p data-testid="tour-savings" className="text-sm text-stone-600">
          {plan.message ?? "No shorter route was found."}
        </p>
      )}
      <ol className="space-y-1 text-sm" data-testid="tour-order">
        {plan.optimized_order.map((stop) => (
          <li key={stop.location_id}>
            {stop.position}. {stop.name}
            <span className="text-stone-500"> · {stop.floor}</span>
          </li>
        ))}
      </ol>
      <button
        type="button"
        data-testid="tour-start-route"
        onClick={onStart}
        className="w-full rounded-lg border border-stone-900 px-3 py-2 text-sm font-semibold text-stone-900"
      >
        Start route
      </button>
      <button type="button" className="text-xs text-stone-600 underline" onClick={onToggle}>
        {details ? "Hide details" : "Details"}
      </button>
      {details ? (
        <div data-testid="tour-details" className="space-y-1 text-xs text-stone-600">
          <p>Algorithm: {algorithmLabel(plan.algorithm)}</p>
          <p>A* pair calculations: {plan.astar_calls}</p>
          <p>2-opt improvements: {plan.two_opt_moves}</p>
          <p>Nearest neighbor: {formatMeters(plan.nearest_neighbor_distance_m)}</p>
          <p>Nearest neighbor + 2-opt: {formatMeters(plan.nearest_neighbor_2opt_distance_m)}</p>
          {plan.exact_distance_m !== null ? (
            <p>
              Exact (Held-Karp): {formatMeters(plan.exact_distance_m)}
              {plan.nearest_neighbor_2opt_gap_percent !== null
                ? ` · 2-opt is ${plan.nearest_neighbor_2opt_gap_percent}% above optimum`
                : ""}
            </p>
          ) : (
            <p>Exact solver skipped at this size.</p>
          )}
          {plan.labels.length > 0 ? <CostMatrix labels={plan.labels} matrix={plan.matrix_m} /> : null}
        </div>
      ) : null}
    </div>
  );
}

function CostMatrix({ labels, matrix }: { labels: string[]; matrix: Array<Array<number | null>> }) {
  return (
    <div className="overflow-x-auto" data-testid="tour-matrix">
      <table className="border-collapse text-[10px]">
        <thead>
          <tr>
            <th className="p-1" />
            {labels.map((label) => (
              <th key={label} className="p-1 text-start font-medium">
                {label}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {matrix.map((row, rowIndex) => (
            <tr key={labels[rowIndex] ?? rowIndex}>
              <th className="p-1 text-start font-medium">{labels[rowIndex]}</th>
              {row.map((cell, column) => (
                <td key={`${rowIndex}-${column}`} className="p-1 tabular-nums">
                  {cell === null ? "—" : cell.toFixed(0)}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function formatMeters(meters: number): string {
  if (meters >= 1000) return `${(meters / 1000).toFixed(2)} km`;
  return `${meters.toFixed(1)} m`;
}

function formatSavedTime(seconds: number): string {
  if (seconds < 90) return `${Math.round(seconds)} s`;
  return formatDuration(seconds);
}

function algorithmLabel(algorithm: string): string {
  if (algorithm === "held_karp") return "Held-Karp (exact)";
  if (algorithm === "nearest_neighbor_2opt") return "Nearest neighbor + 2-opt";
  return "Submitted order";
}
