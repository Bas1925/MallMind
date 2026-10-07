"use client";

import { categoryFill, toSvg, type Bounds } from "@/lib/map-geometry";
import type { MapLocation } from "@/types/map";

interface LocationMarkerProps {
  location: MapLocation;
  bounds: Bounds;
  selected: boolean;
  isStart: boolean;
  isEnd: boolean;
  stopNumber: number | null;
  onSelect: (id: string) => void;
}

export function LocationMarker({
  location,
  bounds,
  selected,
  isStart,
  isEnd,
  stopNumber,
  onSelect,
}: LocationMarkerProps) {
  if (location.x === null || location.y === null) return null;
  const p = toSvg(location.x, location.y, bounds);
  const fill = isStart ? "#15803d" : isEnd ? "#c2410c" : categoryFill(location.category_slug);
  const label = shortLabel(location);

  return (
    <g
      transform={`translate(${p.x} ${p.y})`}
      className="cursor-pointer"
      onClick={(event) => {
        event.stopPropagation();
        onSelect(location.id);
      }}
    >
      <title>{location.name}</title>
      <circle
        r={selected || isStart || isEnd ? 2.8 : 2.1}
        fill={fill}
        stroke={selected ? "#111827" : "#fff"}
        strokeWidth={selected ? 0.7 : 0.4}
      />
      <text
        y={-3.4}
        textAnchor="middle"
        className="pointer-events-none fill-stone-800"
        style={{ fontSize: 2.6, fontWeight: 600 }}
      >
        {label}
      </text>
      {stopNumber !== null ? (
        <g>
          <circle cy={3.6} r={1.8} fill="#111827" />
          <text
            y={4.3}
            textAnchor="middle"
            fill="#fff"
            style={{ fontSize: 2.1, fontWeight: 700 }}
          >
            {stopNumber}
          </text>
        </g>
      ) : null}
    </g>
  );
}

function shortLabel(location: MapLocation): string {
  if (location.category_slug === "restroom") return "WC";
  if (location.category_slug === "atm") return "ATM";
  if (location.category_slug === "elevator") return "Elev";
  if (location.category_slug === "escalator") return "Esc";
  if (location.category_slug === "entrance") {
    return location.slug.includes("parking") ? "Park" : "Main";
  }
  if (location.category_slug === "stairs") return "St";
  return location.name;
}
