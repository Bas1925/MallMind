"use client";

import { Icon } from "@/components/ui/Icon";
import { categoryFill } from "@/lib/map-geometry";
import type { MapLocation } from "@/types/map";

interface LocationCardProps {
  location: MapLocation;
  onNavigate: () => void;
  onSetStart: () => void;
}

export function LocationCard({ location, onNavigate, onSetStart }: LocationCardProps) {
  const tint = categoryFill(location.category_slug);
  return (
    <section data-testid="location-card" className="card rise">
      <div className="flex items-start gap-3">
        <span
          className="mt-0.5 flex h-10 w-10 shrink-0 items-center justify-center rounded-xl"
          style={{ background: `${tint}1f`, color: tint }}
          aria-hidden
        >
          <Icon name="pin" size={18} />
        </span>
        <div className="min-w-0">
          <h2 className="font-display text-2xl leading-tight text-mist-50">{location.name}</h2>
          <p className="mt-0.5 text-xs text-mist-400">
            {location.category_name} · {location.floor_name}
          </p>
        </div>
      </div>
      {location.description ? (
        <p className="mt-3 text-sm leading-relaxed text-mist-200">{location.description}</p>
      ) : null}
      <div className="mt-4 grid grid-cols-2 gap-2">
        <button type="button" className="btn-primary py-2 text-xs" onClick={onNavigate}>
          Navigate here
        </button>
        <button type="button" className="btn-ghost" onClick={onSetStart}>
          Set as start
        </button>
      </div>
    </section>
  );
}
