"use client";

import { useId, useMemo, useState } from "react";
import { Icon } from "@/components/ui/Icon";
import { filterLocations } from "@/lib/location-search";
import type { MapLocation, RouteProfile, SearchAlgorithm } from "@/types/map";

interface RouteFormProps {
  locations: MapLocation[];
  fromId: string;
  toId: string;
  profile: RouteProfile;
  algorithm: SearchAlgorithm;
  loading: boolean;
  onFrom: (id: string) => void;
  onTo: (id: string) => void;
  onProfile: (profile: RouteProfile) => void;
  onAlgorithm: (algorithm: SearchAlgorithm) => void;
  onMazeExample: () => void;
  onSubmit: () => void;
  onSwap: () => void;
}

export const PROFILE_OPTIONS = [
  ["normal", "Walking", "Stairs are allowed. This is the usual route."],
  ["wheelchair", "Wheelchair", "Step-free paths and elevators only."],
  ["avoid_stairs", "No stairs", "Elevators and escalators. Stairs stay closed."],
] as const;

const SEARCH_OPTIONS = [
  ["astar", "Shortest walk", "A* aims at the destination and keeps the shortest distance."],
  ["bfs", "Fewest steps", "Breadth-first checks every nearby hallway before going further."],
  ["dfs", "First hallway", "Depth-first follows one hallway to the end, then turns back."],
] as const;

export function RouteForm({
  locations,
  fromId,
  toId,
  profile,
  algorithm,
  loading,
  onFrom,
  onTo,
  onProfile,
  onAlgorithm,
  onMazeExample,
  onSubmit,
  onSwap,
}: RouteFormProps) {
  return (
    <form
      className="route-form flex flex-col gap-6"
      onSubmit={(event) => {
        event.preventDefault();
        onSubmit();
      }}
    >
      <div className="route-location-card relative flex gap-3 rounded-2xl border border-ink-600 bg-ink-850 p-4">
        <div className="flex w-3 shrink-0 flex-col items-center pb-[19px] pt-[37px]" aria-hidden>
          <span className="h-2.5 w-2.5 shrink-0 rounded-full border-2 border-gold-400 bg-ink-900" />
          <span className="my-2 w-px flex-1 border-s border-dashed border-ink-600" />
          <span className="h-2.5 w-2.5 shrink-0 rounded-sm bg-gold-400" />
        </div>
        <div className="flex min-w-0 flex-1 flex-col gap-5">
          <PlaceField
            label="From"
            testId="from-select"
            placeholder="Type a starting place"
            value={fromId}
            locations={locations}
            onChange={onFrom}
          />
          <PlaceField
            label="To"
            testId="to-select"
            placeholder="Type a destination"
            value={toId}
            locations={locations}
            onChange={onTo}
          />
        </div>
        <button
          type="button"
          aria-label="Swap start and destination"
          title="Swap start and destination"
          className="absolute end-7 top-1/2 z-10 inline-flex h-8 w-8 -translate-y-1/2 items-center justify-center rounded-full border border-ink-600 bg-ink-900 text-mist-300 shadow-sm transition hover:border-gold-400 hover:text-gold-400 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-gold-400 focus-visible:ring-offset-2"
          onClick={onSwap}
        >
          <Icon name="swap" size={15} />
        </button>
      </div>

      <ChoiceGroup
        legend="How you walk"
        name="profile"
        value={profile}
        options={PROFILE_OPTIONS}
        onChange={onProfile}
      />
      <ChoiceGroup
        legend="How to search"
        name="algorithm"
        value={algorithm}
        options={SEARCH_OPTIONS}
        onChange={onAlgorithm}
      />
      <button type="button" className="btn-ghost min-h-11 text-left" onClick={onMazeExample}>
        Open the search maze
      </button>

      <button
        type="submit"
        data-testid="route-submit"
        disabled={loading || fromId === "" || toId === ""}
        className="btn-primary min-h-12"
      >
        <Icon name="route" size={16} />
        {loading ? "Finding route…" : "Show route"}
      </button>
    </form>
  );
}

function ChoiceGroup<T extends string>({
  legend,
  name,
  value,
  options,
  onChange,
}: {
  legend: string;
  name: string;
  value: T;
  options: readonly (readonly [T, string, string])[];
  onChange: (value: T) => void;
}) {
  const selected = options.find(([option]) => option === value);
  return (
    <fieldset className="min-w-0">
      <legend className="mb-2 text-sm font-semibold text-mist-50">{legend}</legend>
      <div className="flex flex-col gap-2">
        {options.map(([option, label]) => (
          <label
            key={option}
            className={`flex min-h-12 cursor-pointer items-center gap-3 rounded-xl border px-3 py-2 text-sm focus-within:ring-2 focus-within:ring-gold-400 focus-within:ring-offset-2 ${
              value === option
                ? "border-gold-400 bg-gold-400/[0.07] text-mist-50"
                : "border-ink-600 bg-ink-900 text-mist-200"
            }`}
          >
            <input
              type="radio"
              name={name}
              value={option}
              checked={value === option}
              onChange={() => onChange(option)}
              className="h-4 w-4 accent-gold-400"
            />
            <span className="font-medium">{label}</span>
          </label>
        ))}
      </div>
      <p className="mt-2 text-sm leading-relaxed text-mist-200">{selected?.[2]}</p>
    </fieldset>
  );
}

function PlaceField({
  label,
  testId,
  placeholder,
  value,
  locations,
  onChange,
}: {
  label: string;
  testId: string;
  placeholder: string;
  value: string;
  locations: MapLocation[];
  onChange: (id: string) => void;
}) {
  const selected = locations.find((loc) => loc.id === value);
  const selectedLabel = selected === undefined ? "" : `${selected.name} · ${selected.floor_name}`;
  const [draft, setDraft] = useState<string | null>(null);
  const [active, setActive] = useState(0);
  const listId = useId();
  const editing = draft !== null;
  const query = draft ?? "";
  const matches = useMemo(
    () => (editing ? filterLocations(locations, query, 8) : []),
    [editing, locations, query],
  );
  const open = editing && query.trim() !== "" && matches.length > 0;
  const activeIndex = matches.length === 0 ? 0 : Math.min(active, matches.length - 1);

  function choose(id: string): void {
    onChange(id);
    setDraft(null);
    setActive(0);
    if (document.activeElement instanceof HTMLElement) document.activeElement.blur();
  }

  return (
    <div className="relative min-w-0">
      <label className="flex min-w-0 flex-col gap-1.5">
        <span className="text-xs font-medium text-mist-300">{label}</span>
        <input
          data-testid={testId}
          data-location-id={value}
          role="combobox"
          aria-autocomplete="list"
          aria-expanded={open}
          aria-controls={open ? listId : undefined}
          aria-activedescendant={open ? `${listId}-${activeIndex}` : undefined}
          autoComplete="off"
          placeholder={placeholder}
          className={`field min-h-11 pe-6 ${editing || value === "" ? "" : "font-medium"}`}
          value={editing ? query : selectedLabel}
          onFocus={() => {
            setDraft("");
            setActive(0);
          }}
          onBlur={() => setDraft(null)}
          onChange={(event) => {
            setDraft(event.target.value);
            setActive(0);
          }}
          onKeyDown={(event) => {
            if (event.key === "Escape") {
              setDraft(null);
              return;
            }
            if (matches.length === 0) return;
            if (event.key === "ArrowDown" || event.key === "ArrowUp") {
              event.preventDefault();
              const delta = event.key === "ArrowDown" ? 1 : -1;
              setActive((index) => (index + delta + matches.length) % matches.length);
            } else if (event.key === "Enter" && open) {
              event.preventDefault();
              const match = matches[activeIndex];
              if (match !== undefined) choose(match.id);
            }
          }}
        />
      </label>
      {open ? (
        <ul
          id={listId}
          role="listbox"
          aria-label={`${label} matches`}
          data-testid={`${testId}-results`}
          className="scroll-thin absolute z-20 mt-1 max-h-56 w-full overflow-auto rounded-xl border border-ink-600 bg-white p-1 shadow-glass"
        >
          {matches.map((loc, index) => (
            <li key={loc.id} role="none">
              <button
                id={`${listId}-${index}`}
                type="button"
                role="option"
                aria-selected={index === activeIndex}
                tabIndex={-1}
                className={`flex w-full flex-col rounded-lg px-3 py-2 text-start ${index === activeIndex ? "bg-ink-850" : ""}`}
                onMouseDown={(event) => {
                  event.preventDefault();
                  choose(loc.id);
                }}
                onClick={() => choose(loc.id)}
                onMouseEnter={() => setActive(index)}
              >
                <span className="truncate text-sm font-medium text-mist-50">{loc.name}</span>
                <span className="text-xs text-mist-400">{loc.category_name} · {loc.floor_name}</span>
              </button>
            </li>
          ))}
        </ul>
      ) : null}
      {editing && query.trim() !== "" && matches.length === 0 ? (
        <p role="status" className="mt-1 text-xs text-mist-400">No places match. Try a shorter name.</p>
      ) : null}
    </div>
  );
}
