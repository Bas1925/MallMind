"use client";

import type { MapLocation } from "@/types/map";

interface LocationCardProps {
  location: MapLocation;
  onNavigate: () => void;
  onSetStart: () => void;
}

export function LocationCard({ location, onNavigate, onSetStart }: LocationCardProps) {
  return (
    <section data-testid="location-card" className="rounded-xl border border-stone-200 bg-white p-4">
      <h2 className="text-base font-semibold text-stone-900">{location.name}</h2>
      <p className="mt-1 text-sm text-stone-500">
        {location.category_name} · {location.floor_name}
      </p>
      {location.description ? (
        <p className="mt-2 text-sm text-stone-600">{location.description}</p>
      ) : null}
      <div className="mt-3 flex flex-wrap gap-2">
        <button
          type="button"
          className="rounded-lg bg-stone-900 px-3 py-1.5 text-xs font-semibold text-white"
          onClick={onNavigate}
        >
          Navigate here
        </button>
        <button
          type="button"
          className="rounded-lg border border-stone-200 px-3 py-1.5 text-xs font-semibold text-stone-700"
          onClick={onSetStart}
        >
          Set as start
        </button>
      </div>
    </section>
  );
}
