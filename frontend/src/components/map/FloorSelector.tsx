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
    <div className="flex gap-0.5 rounded-xl border border-[#dfe4dc] bg-white p-1 shadow-[0_2px_8px_rgba(36,60,53,0.04)]" role="tablist" aria-label="Floor">
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
            className={`relative whitespace-nowrap rounded-lg px-3 py-2 text-[11px] font-semibold transition sm:px-4 sm:text-xs ${
              active
                ? "bg-[#243c35] text-white"
                : "text-[#77827a] hover:bg-[#f4f6f1] hover:text-[#243c35]"
            }`}
          >
            {floor.name}
            {onRoute && !active ? (
              <span
                className="absolute end-1.5 top-1.5 h-1 w-1 rounded-full bg-[#176b52]"
                aria-hidden
              />
            ) : null}
          </button>
        );
      })}
    </div>
  );
}
