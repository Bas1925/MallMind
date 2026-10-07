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
    <div
      className="flex gap-1 rounded-full border border-stone-200 bg-white/95 p-1 shadow-sm"
      role="tablist"
      aria-label="Floor"
    >
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
            className={
              active
                ? "rounded-full bg-stone-900 px-3 py-1.5 text-xs font-semibold text-white"
                : "rounded-full px-3 py-1.5 text-xs font-medium text-stone-600 hover:bg-stone-100"
            }
          >
            {floor.name}
            {onRoute && !active ? (
              <span className="ms-1 inline-block h-1.5 w-1.5 rounded-full bg-orange-500" aria-hidden />
            ) : null}
          </button>
        );
      })}
    </div>
  );
}
