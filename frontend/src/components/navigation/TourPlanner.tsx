"use client";

import { type Dispatch, type SetStateAction, type KeyboardEvent, useEffect, useMemo, useRef, useState } from "react";
import { optimizeTour } from "@/lib/api";
import { Icon } from "@/components/ui/Icon";
import { categoryFill, formatDuration } from "@/lib/map-geometry";
import type { MapLocation, RouteProfile } from "@/types/map";
import type { OptimizeResponse } from "@/types/tour";

interface TourPlannerProps {
  locations: MapLocation[];
  profile: RouteProfile;
  onProfile: (profile: RouteProfile) => void;
  onApply: (plan: OptimizeResponse) => void;
  onInvalidate?: () => void;
  stopIds?: string[];
  onStopIdsChange?: Dispatch<SetStateAction<string[]>>;
}

const PROFILES: Array<{ id: RouteProfile; label: string }> = [
  { id: "normal", label: "Walking" },
  { id: "wheelchair", label: "Wheelchair" },
  { id: "avoid_stairs", label: "Avoid stairs" },
];

export function TourPlanner({ locations, profile, onProfile, onApply, onInvalidate, stopIds: controlledStops, onStopIdsChange }: TourPlannerProps) {
  const entrance = locations.find((loc) => loc.slug === "main-entrance");
  const [startId, setStartId] = useState(entrance?.id ?? locations[0]?.id ?? "");
  const [localStops, setLocalStops] = useState<string[]>([]);
  const stopIds = controlledStops ?? localStops;
  const setStopIds = onStopIdsChange ?? setLocalStops;
  const [query, setQuery] = useState("");
  const [active, setActive] = useState(0);
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [plan, setPlan] = useState<OptimizeResponse | null>(null);
  const [details, setDetails] = useState(false);
  const revision = useRef(0);
  useEffect(() => () => { revision.current += 1; }, []);
  useEffect(() => {
    revision.current += 1;
    setPending(false);
    setPlan(null);
    setError(null);
  }, [stopIds]);
  useEffect(() => {
    // A stop added from the directory may already be the chosen origin.
    if (stopIds.includes(startId)) setStopIds((ids) => ids.filter((id) => id !== startId));
  }, [startId, stopIds, setStopIds]);

  function invalidate(): void {
    revision.current += 1;
    setPending(false);
    setPlan(null);
    setError(null);
    onInvalidate?.();
  }

  const byId = useMemo(() => new Map(locations.map((loc) => [loc.id, loc])), [locations]);
  const choices = locations.filter((loc) => {
    if (loc.id === startId || stopIds.includes(loc.id)) return false;
    const q = query.trim().toLowerCase();
    if (q === "") return true;
    return loc.name.toLowerCase().includes(q) || loc.category_name.toLowerCase().includes(q);
  });

  const visible = query.trim() === "" ? [] : choices.slice(0, 6);

  function addStop(id: string): void {
    invalidate();
    setStopIds((ids) => [...ids, id]);
    setQuery("");
    setActive(0);
  }

  function onStopKey(event: KeyboardEvent<HTMLInputElement>): void {
    if (visible.length === 0) return;
    if (event.key === "ArrowDown") {
      event.preventDefault();
      setActive((index) => (index + 1) % visible.length);
    } else if (event.key === "ArrowUp") {
      event.preventDefault();
      setActive((index) => (index - 1 + visible.length) % visible.length);
    } else if (event.key === "Enter") {
      event.preventDefault();
      const pick = visible[Math.min(active, visible.length - 1)];
      if (pick !== undefined) addStop(pick.id);
    } else if (event.key === "Escape") {
      setQuery("");
      setActive(0);
    }
  }

  async function optimize(): Promise<void> {
    if (startId === "" || stopIds.length === 0) return;
    const requestRevision = ++revision.current;
    setPending(true);
    setPlan(null);
    setError(null);
    try {
      const result = await optimizeTour({
        startLocationId: startId,
        locationIds: stopIds,
        profile,
      });
      if (requestRevision !== revision.current) return;
      setPlan(result);
      onApply(result);
    } catch (err) {
      if (requestRevision !== revision.current) return;
      setPlan(null);
      setError(err instanceof Error ? err.message : "Could not optimize the route");
    } finally {
      if (requestRevision === revision.current) setPending(false);
    }
  }

  function move(index: number, delta: number): void {
    const next = index + delta;
    if (next < 0 || next >= stopIds.length) return;
    const copy = [...stopIds];
    const current = copy[index];
    const swap = copy[next];
    if (current === undefined || swap === undefined) return;
    invalidate();
    copy[index] = swap;
    copy[next] = current;
    setStopIds(copy);
  }

  return (
    <section className="space-y-5" data-testid="tour-planner" aria-labelledby="tour-title">
      <div className="flex items-start gap-3">
        <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl border border-gold-400/15 bg-gold-400/[0.07] text-gold-400" aria-hidden>
          <Icon name="list" size={20} />
        </span>
        <div>
          <h2 id="tour-title" className="text-lg font-semibold tracking-tight text-mist-50">Plan your visit</h2>
          <p className="mt-1 text-xs leading-relaxed text-mist-400">All your stops, in one easy route.</p>
        </div>
      </div>
      <label className="flex flex-col gap-1.5">
        <span className="text-xs font-medium text-mist-300">Start</span>
        <select
          data-testid="tour-start"
          value={startId}
          onChange={(event) => {
            invalidate();
            setStartId(event.target.value);
            setStopIds((ids) => ids.filter((id) => id !== event.target.value));
          }}
          className="field cursor-pointer"
        >
          {locations.map((loc) => (
            <option key={loc.id} value={loc.id}>
              {loc.name} · {loc.floor_name}
            </option>
          ))}
        </select>
      </label>

      <div className="relative flex flex-col gap-1.5">
        <label htmlFor="tour-search" className="text-xs font-medium text-mist-300">Stops</label>
        <div className="relative">
          <Icon
            name="search"
            size={15}
            className="pointer-events-none absolute start-3.5 top-1/2 -translate-y-1/2 text-mist-500"
          />
          <input
            id="tour-search"
            data-testid="tour-search"
            value={query}
            onChange={(event) => {
              setQuery(event.target.value);
              setActive(0);
            }}
            onKeyDown={onStopKey}
            role="combobox"
            aria-expanded={visible.length > 0}
            aria-controls="tour-choices"
            aria-activedescendant={visible.length > 0 ? `tour-choice-${active}` : undefined}
            placeholder="Add Nike, an ATM, a pharmacy…"
            className="field ps-10"
          />
        </div>
        {visible.length > 0 ? (
          <ul
            id="tour-choices"
            role="listbox"
            className="scroll-thin max-h-52 overflow-auto rounded-xl border border-ink-600 bg-ink-900 p-1 shadow-glass"
          >
            {visible.map((loc, index) => (
              <li key={loc.id} id={`tour-choice-${index}`} role="option" aria-selected={index === active}>
                <button
                  type="button"
                  tabIndex={-1}
                  className={`flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-start transition ${
                    index === active ? "bg-gold-400/[0.08]" : "hover:bg-ink-850"
                  }`}
                  onMouseEnter={() => setActive(index)}
                  onClick={() => addStop(loc.id)}
                >
                  <span
                    className="h-2 w-2 shrink-0 rounded-full"
                    style={{ background: categoryFill(loc.category_slug) }}
                    aria-hidden
                  />
                  <span className="flex min-w-0 flex-col">
                    <span className="truncate text-sm font-medium text-mist-50">{loc.name}</span>
                    <span className="text-[11px] text-mist-500">
                      {loc.category_name} · {loc.floor_name}
                    </span>
                  </span>
                  {index === active ? (
                    <kbd className="ms-auto rounded border border-ink-600 bg-ink-900 px-1.5 py-0.5 text-[10px] text-mist-400">
                      ↵
                    </kbd>
                  ) : null}
                </button>
              </li>
            ))}
          </ul>
        ) : null}
      </div>

      {stopIds.length > 0 ? (
        <ol data-testid="tour-stops" className="space-y-1.5">
          {stopIds.map((id, index) => {
            const loc = byId.get(id);
            const name = loc?.name ?? "stop";
            return (
              <li
                key={id}
                className="rise flex items-center gap-1.5 rounded-xl border border-ink-600 bg-ink-850 py-2 pe-1.5 ps-2.5 text-sm"
              >
                <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-gold-400/[0.08] text-[11px] font-semibold text-gold-400">
                  {index + 1}
                </span>
                <span className="min-w-0 flex-1 truncate text-xs font-medium text-mist-50">{loc?.name ?? id}</span>
                <button
                  type="button"
                  aria-label={`Move ${name} up`}
                  className="icon-btn h-8 w-8"
                  disabled={index === 0}
                  onClick={() => move(index, -1)}
                >
                  <Icon name="up" size={14} />
                </button>
                <button
                  type="button"
                  aria-label={`Move ${name} down`}
                  className="icon-btn h-8 w-8"
                  disabled={index === stopIds.length - 1}
                  onClick={() => move(index, 1)}
                >
                  <Icon name="down" size={14} />
                </button>
                <button
                  type="button"
                  aria-label={`Remove ${name}`}
                  className="icon-btn h-8 w-8 hover:text-rose-400"
                  onClick={() => { invalidate(); setStopIds((ids) => ids.filter((item) => item !== id)); }}
                >
                  <Icon name="close" size={14} />
                </button>
              </li>
            );
          })}
        </ol>
      ) : (
        <p className="rounded-xl border border-dashed border-ink-600 bg-ink-850 px-4 py-5 text-center text-xs leading-relaxed text-mist-400">
          Add the stores you want to visit, in any order.
          <br />
                Find an efficient walk between every stop.
        </p>
      )}

      <fieldset className="grid grid-cols-3 gap-1.5">
        <legend className="mb-2.5 text-xs font-medium text-mist-300">Route profile</legend>
        {PROFILES.map((item) => (
          <label key={item.id} className={`chip justify-center !px-1.5 !py-2.5 ${profile === item.id ? "chip-active" : ""}`}>
            <input
              type="radio"
              name="tour-profile"
              value={item.id}
              checked={profile === item.id}
              onChange={() => { invalidate(); onProfile(item.id); }}
              className="sr-only"
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
        className="btn-primary min-h-12"
      >
        <Icon name="sparkle" size={15} />
        {pending ? "Optimizing…" : "Optimize route"}
      </button>

      {error !== null ? (
        <p
          data-testid="tour-error"
          role="alert"
          className="rounded-xl border border-rose-400/30 bg-rose-400/10 px-3 py-2 text-sm text-rose-400"
        >
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
    <div className="rise space-y-4 border-t border-ink-600 pt-5" data-testid="tour-result">
      <div className="grid grid-cols-2 gap-2">
        <div className="rounded-xl border border-ink-600 bg-ink-850 p-3.5">
          <p className="eyebrow">Your order</p>
          <p className="mt-2 text-xl font-semibold tracking-tight text-mist-400 line-through decoration-mist-400/50">
            {formatMeters(plan.original_distance_m)}
          </p>
          <p className="text-xs text-mist-500">{formatDuration(plan.original_seconds)}</p>
        </div>
        <div className="rounded-xl border border-gold-400/30 bg-gold-400/[0.06] p-3.5">
          <p className="eyebrow !text-gold-300">Optimized</p>
          <p className="mt-2 text-xl font-semibold tracking-tight text-gold-400">
            {formatMeters(plan.optimized_distance_m)}
          </p>
          <p className="text-xs text-mist-400">{formatDuration(plan.optimized_seconds)}</p>
        </div>
      </div>
      {plan.improved ? (
        <p
          data-testid="tour-savings"
          className="flex items-center gap-2 rounded-xl border border-jade-400/15 bg-jade-400/[0.07] px-3 py-3 text-xs font-medium leading-relaxed text-jade-400"
        >
          <Icon name="sparkle" size={14} />
          You save {formatMeters(plan.distance_saved_m)}
          {plan.distance_saved_percent !== null ? ` · ${plan.distance_saved_percent}%` : ""}
          {plan.estimated_time_saved_seconds > 0
            ? ` · ${formatSavedTime(plan.estimated_time_saved_seconds)}`
            : ""}
        </p>
      ) : (
        <p data-testid="tour-savings" className="text-sm text-mist-400">
          {plan.message ?? "No shorter route was found."}
        </p>
      )}
      <ol data-testid="tour-order">
        {plan.optimized_order.map((stop, i) => (
          <li key={stop.location_id} className="relative flex items-center gap-3 pb-2.5">
            {i < plan.optimized_order.length - 1 ? (
              <span className="absolute start-[11px] top-6 h-[calc(100%-1rem)] w-px bg-gold-400/25" aria-hidden />
            ) : null}
            <span
              className={`relative z-10 flex h-6 w-6 shrink-0 items-center justify-center rounded-full text-[11px] font-bold text-white ${
                i === 0 ? "bg-jade-400" : "bg-gold-300"
              }`}
              aria-hidden
            >
              {stop.position}
            </span>
            <span className="text-[13px] leading-relaxed text-mist-50">
              <span className="sr-only">{stop.position}. </span>
              {stop.name}
              <span className="text-mist-500"> · {stop.floor}</span>
            </span>
          </li>
        ))}
      </ol>
      <div className="flex gap-2">
        <button
          type="button"
          data-testid="tour-start-route"
          onClick={onStart}
          className="btn-primary flex-1"
        >
          Start route
        </button>
        <button type="button" className="btn-ghost" onClick={onToggle}>
          {details ? "Hide details" : "Details"}
        </button>
      </div>
      {details ? (
        <div data-testid="tour-details" className="card space-y-1.5 !bg-ink-850 font-mono text-[11px] leading-relaxed text-mist-300">
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
      <table className="mt-3 w-full border-collapse text-[10px] text-mist-200">
        <thead className="border-b border-ink-600 bg-ink-700/50">
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
            <tr key={labels[rowIndex] ?? rowIndex} className="border-b border-ink-600/60 last:border-0">
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
