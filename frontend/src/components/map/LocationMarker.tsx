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
  const fill = isStart ? "#3ddc97" : isEnd ? "#ff6b81" : categoryFill(location.category_slug);
  const label = shortLabel(location);
  const emphasis = selected || isStart || isEnd;
  const utility = isUtility(location);

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
      {selected ? <circle r={4} fill="none" stroke="#f2cf8a" strokeWidth={0.5} /> : null}
      <circle r={emphasis ? 2.6 : 2.1} fill="#0b0e14" stroke={fill} strokeWidth={0.7} />
      <circle r={emphasis ? 1.35 : 1} fill={fill} />
      <text
        y={-3.6}
        textAnchor="middle"
        className="pointer-events-none"
        fill={utility ? "#9aa0ab" : "#f6f4ef"}
        stroke="#10141c"
        strokeWidth={0.9}
        paintOrder="stroke"
        style={{ fontSize: utility ? 2.1 : 2.5, fontWeight: utility ? 500 : 600, letterSpacing: 0.05 }}
      >
        {label}
      </text>
      {stopNumber !== null ? (
        <g transform="translate(2.6 2.6)">
          <circle r={1.9} fill="#f2cf8a" stroke="#0b0e14" strokeWidth={0.4} />
          <text y={0.75} textAnchor="middle" fill="#07090d" style={{ fontSize: 2.1, fontWeight: 800 }}>
            {stopNumber}
          </text>
        </g>
      ) : null}
    </g>
  );
}

function isUtility(location: MapLocation): boolean {
  return ["restroom", "atm", "elevator", "escalator", "stairs"].includes(location.category_slug);
}

function shortLabel(location: MapLocation): string {
  if (location.category_slug === "restroom") return "WC";
  if (location.category_slug === "atm") return "ATM";
  if (location.category_slug === "elevator") return "Lift";
  if (location.category_slug === "escalator") return "Escalator";
  if (location.category_slug === "entrance") {
    return location.slug.includes("parking") ? "Parking" : "Entrance";
  }
  if (location.category_slug === "stairs") return "Stairs";
  return location.name;
}
