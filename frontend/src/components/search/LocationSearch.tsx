"use client";

import { useEffect, useMemo, useState } from "react";
import { searchLocations } from "@/lib/api";
import { filterLocations } from "@/lib/location-search";
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
      <label className="flex flex-col gap-1 text-xs font-medium text-stone-600">
        Search
        <input
          data-testid="location-search"
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          placeholder="Nike, bathroom, ATM…"
          className="rounded-lg border border-stone-200 bg-white px-3 py-2 text-sm text-stone-900"
        />
      </label>
      {results.length > 0 ? (
        <ul
          data-testid="search-results"
          className="absolute z-10 mt-1 max-h-56 w-full overflow-auto rounded-lg border border-stone-200 bg-white shadow-md"
        >
          {results.map((loc) => (
            <li key={loc.id}>
              <button
                type="button"
                className="flex w-full flex-col items-start px-3 py-2 text-start hover:bg-stone-50"
                onClick={() => {
                  onPick(loc.id);
                  setQuery("");
                }}
              >
                <span className="text-sm font-medium text-stone-900">{loc.name}</span>
                <span className="text-xs text-stone-500">
                  {loc.category} · {loc.floor}
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
    });
  }
  return rows;
}
