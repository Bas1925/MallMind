"use client";

import { useEffect, useId, useMemo, useState } from "react";
import { searchLocations } from "@/lib/api";
import { Icon } from "@/components/ui/Icon";
import { filterLocations } from "@/lib/location-search";
import { categoryFill } from "@/lib/map-geometry";
import type { SearchHit } from "@/types/assistant";
import type { MapLocation } from "@/types/map";

interface LocationSearchProps {
  locations: MapLocation[];
  onPick: (id: string) => void;
}

interface ResultRow {
  id: string;
  name: string;
  category: string;
  floor: string;
  categorySlug: string;
}

export function LocationSearch({ locations, onPick }: LocationSearchProps) {
  const [query, setQuery] = useState("");
  const [remote, setRemote] = useState<SearchHit[]>([]);
  const [open, setOpen] = useState(false);
  const [active, setActive] = useState(0);
  const [pending, setPending] = useState(false);
  const listId = useId();
  const local = useMemo(() => filterLocations(locations, query), [locations, query]);

  useEffect(() => {
    const trimmed = query.trim();
    if (trimmed.length < 2) {
      setRemote([]);
      setPending(false);
      return;
    }
    const controller = new AbortController();
    setPending(true);
    const handle = window.setTimeout(() => {
      searchLocations(trimmed, controller.signal)
        .then((hits) => { if (!controller.signal.aborted) setRemote(hits); })
        .catch(() => { if (!controller.signal.aborted) setRemote([]); })
        .finally(() => { if (!controller.signal.aborted) setPending(false); });
    }, 250);
    return () => { window.clearTimeout(handle); controller.abort(); };
  }, [query]);

  const results = useMemo(() => mergeResults(local, remote), [local, remote]);
  const expanded = open && query.trim() !== "" && results.length > 0;
  const activeIndex = Math.min(active, results.length - 1);

  function pick(id: string): void {
    onPick(id);
    setQuery("");
    setRemote([]);
    setOpen(false);
    setActive(0);
  }

  return (
    <div className="relative">
      <label className="relative block">
        <span className="sr-only">Search</span>
        <Icon
          name="search"
          size={16}
          className="pointer-events-none absolute start-3.5 top-1/2 -translate-y-1/2 text-mist-500"
        />
        <input
          data-testid="location-search"
          value={query}
          role="combobox"
          aria-autocomplete="list"
          aria-expanded={expanded}
          aria-controls={expanded ? listId : undefined}
          aria-activedescendant={expanded ? `${listId}-${activeIndex}` : undefined}
          autoComplete="off"
          onFocus={() => setOpen(true)}
          onBlur={() => setOpen(false)}
          onChange={(event) => {
            setQuery(event.target.value);
            setRemote([]);
            setOpen(true);
            setActive(0);
          }}
          onKeyDown={(event) => {
            if (event.key === "Escape") { setOpen(false); return; }
            if (results.length === 0) return;
            if (event.key === "ArrowDown" || event.key === "ArrowUp") {
              event.preventDefault();
              setOpen(true);
              const delta = event.key === "ArrowDown" ? 1 : -1;
              setActive((index) => open ? (index + delta + results.length) % results.length : 0);
            } else if (event.key === "Enter" && expanded) {
              event.preventDefault();
              const result = results[activeIndex];
              if (result !== undefined) pick(result.id);
            }
          }}
          placeholder="Search stores, restrooms, ATMs…"
          className="field ps-10"
        />
      </label>
      {expanded ? (
        <ul
          id={listId}
          role="listbox"
          aria-label="Places"
          data-testid="search-results"
          className="scroll-thin absolute z-20 mt-2 max-h-64 w-full overflow-auto rounded-xl border border-ink-600 bg-white p-1 shadow-glass"
        >
          {results.map((loc, index) => (
            <li key={loc.id} role="none">
              <button
                id={`${listId}-${index}`}
                role="option"
                aria-selected={index === activeIndex}
                tabIndex={-1}
                type="button"
                className={`flex w-full items-center gap-3 rounded-lg px-3 py-3 text-start transition hover:bg-ink-850 ${index === activeIndex ? "bg-ink-850" : ""}`}
                onMouseDown={(event) => event.preventDefault()}
                onMouseEnter={() => setActive(index)}
                onClick={() => pick(loc.id)}
              >
                <span
                  className="h-2 w-2 shrink-0 rounded-full"
                  style={{ background: categoryFill(loc.categorySlug) }}
                  aria-hidden
                />
                <span className="flex min-w-0 flex-col">
                  <span className="truncate text-sm font-medium text-mist-50">{loc.name}</span>
                  <span className="text-xs text-mist-500">
                    {loc.category} · {loc.floor}
                  </span>
                </span>
              </button>
            </li>
          ))}
        </ul>
      ) : null}
      {open && query.trim() !== "" && results.length === 0 ? (
        <p role="status" className="mt-2 text-xs text-mist-400">
          {pending ? "Searching…" : "No places found. Try a store name or a service like ATM."}
        </p>
      ) : null}
    </div>
  );
}

function mergeResults(local: MapLocation[], remote: SearchHit[]): ResultRow[] {
  const rows: ResultRow[] = local.map((loc) => ({
    id: loc.id,
    name: loc.name,
    category: loc.category_name,
    floor: loc.floor_name,
    categorySlug: loc.category_slug,
  }));
  const seen = new Set(rows.map((row) => row.id));
  for (const hit of remote) {
    if (seen.has(hit.location_id)) continue;
    seen.add(hit.location_id);
    rows.push({
      id: hit.location_id,
      name: hit.name,
      category: hit.category,
      floor: hit.floor,
      categorySlug: hit.category_slug,
    });
  }
  return rows;
}
