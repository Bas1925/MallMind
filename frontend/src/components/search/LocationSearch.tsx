"use client";

import { useEffect, useMemo, useState } from "react";
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
  const local = useMemo(() => filterLocations(locations, query), [locations, query]);

  useEffect(() => {
    const trimmed = query.trim();
    if (trimmed.length < 2) {
      setRemote([]);
      return;
    }
    const handle = window.setTimeout(() => {
      searchLocations(trimmed)
        .then(setRemote)
        .catch(() => setRemote([]));
    }, 250);
    return () => window.clearTimeout(handle);
  }, [query]);

  const results = useMemo(() => mergeResults(local, remote), [local, remote]);

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
          onChange={(event) => setQuery(event.target.value)}
          placeholder="Search stores, restrooms, ATMs…"
          className="field ps-10"
        />
      </label>
      {results.length > 0 ? (
        <ul
          data-testid="search-results"
          className="scroll-thin absolute z-20 mt-2 max-h-64 w-full overflow-auto rounded-2xl border border-white/[0.08] bg-ink-800/95 p-1 shadow-glass backdrop-blur-xl"
        >
          {results.map((loc) => (
            <li key={loc.id}>
              <button
                type="button"
                className="flex w-full items-center gap-3 rounded-xl px-3 py-2 text-start transition hover:bg-white/[0.05]"
                onClick={() => {
                  onPick(loc.id);
                  setQuery("");
                }}
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
