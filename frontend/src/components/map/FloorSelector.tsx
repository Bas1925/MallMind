"use client";

import type { MapFloor } from "@/types/map";

interface FloorSelectorProps {
  floors: MapFloor[];
  activeLevel: number;
  routeLevels: number[];
  onChange: (level: number) => void;
}

export function FloorSelector({ floors, activeLevel, routeLevels, onChange }: FloorSelectorProps) {
  return (
    <div className="glass flex gap-0.5 rounded-full p-1" role="tablist" aria-label="Floor">
      {floors.map((floor) => {
        const active = floor.level === activeLevel;
        const onRoute = routeLevels.includes(floor.level);
        return (
          <button
            key={floor.id}
            type="button"
            role="tab"
            aria-selected={active}
            onClick={() => onChange(floor.level)}
            className={`relative rounded-full px-3.5 py-1.5 text-xs font-semibold transition ${
              active
                ? "bg-mist-50 text-ink-950 shadow"
                : "text-mist-400 hover:bg-white/[0.06] hover:text-mist-50"
            }`}
          >
            {floor.name}
            {onRoute && !active ? (
              <span
                className="absolute end-1.5 top-1 h-1.5 w-1.5 rounded-full bg-gold-400 shadow-[0_0_8px_rgba(232,184,106,0.9)]"
                aria-hidden
              />
            ) : null}
          </button>
        );
      })}
    </div>
  );
}
