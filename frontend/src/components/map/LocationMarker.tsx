"use client";

import { toSvg, type Bounds } from "@/lib/map-geometry";
import type { MapLocation } from "@/types/map";

interface LocationMarkerProps {
  location: MapLocation;
  bounds: Bounds;
  selected: boolean;
  isStart: boolean;
  isEnd: boolean;
  stopNumber: number | null;
  maxWidth?: number;
  perspective?: boolean;
  onSelect: (id: string) => void;
}

const INK = "#243c35";
const GREEN = "#176b52";

export function LocationMarker({
  location,
  bounds,
  selected,
  isStart,
  isEnd,
  stopNumber,
  maxWidth = 18,
  perspective = true,
  onSelect,
}: LocationMarkerProps) {
  if (location.x === null || location.y === null) return null;
  const p = toSvg(location.x, location.y, bounds);
  const utility = isUtility(location);
  const entrance = location.category_slug === "entrance";
  const emphasized = selected || isStart || isEnd;
  const width = utility ? 8 : entrance ? Math.min(maxWidth, 15) : maxWidth;
  const height = utility ? 8 : entrance ? 9 : 14;
  const palette = tilePalette(location.category_slug);
  const depth = utility || entrance ? 0.7 : 1.4;
  const sideOffset = utility || entrance ? 0.25 : 0.55;
  const label = shortLabel(location);
  const lines = wrapLabel(label, Math.max(7, Math.floor(width / 1.12)));
  const labelSize = Math.min(2.5, (width - 2) / (Math.max(...lines.map((line) => line.length)) * 0.54));

  return (
    <g
      transform={`translate(${p.x} ${p.y})`}
      className="group cursor-pointer outline-none"
      role="button"
      tabIndex={0}
      aria-label={`${location.name}${isStart ? ", route start" : ""}${isEnd ? ", destination" : ""}`}
      aria-pressed={selected}
      onKeyDown={(event) => {
        if (event.key === "Enter" || event.key === " ") {
          event.preventDefault();
          event.stopPropagation();
          onSelect(location.id);
        }
      }}
      onClick={(event) => {
        event.stopPropagation();
        onSelect(location.id);
      }}
    >
      <title>{location.name}</title>
      {perspective ? (
        <rect
          x={-width / 2 + 0.6}
          y={-height / 2 + depth + 0.55}
          width={width + 0.6}
          height={height + 0.6}
          rx={utility ? 2 : 1.5}
          fill="#244f44"
          opacity={selected ? 0.14 : 0.07}
          pointerEvents="none"
        />
      ) : null}
      <g
        className={perspective
          ? `map-marker-volume motion-safe:transition-transform motion-safe:duration-300 motion-safe:ease-out motion-safe:group-hover:-translate-y-[0.75px] motion-safe:group-focus-visible:-translate-y-[0.75px] ${selected ? "-translate-y-[0.6px]" : "translate-y-0"}`
          : undefined}
      >
      {perspective ? (
        <g aria-hidden pointerEvents="none">
          <rect
            x={-width / 2 + sideOffset}
            y={-height / 2 + depth}
            width={width}
            height={height}
            rx={utility ? 1.8 : 1.15}
            fill={palette.side}
          />
          <path
            d={`M ${width / 2 - 1.15} ${-height / 2} L ${width / 2 + sideOffset} ${-height / 2 + depth + 1.15} V ${height / 2 + depth - 1.15} Q ${width / 2 + sideOffset} ${height / 2 + depth} ${width / 2 + sideOffset - 1.15} ${height / 2 + depth} L ${width / 2 - 1.15} ${height / 2} Z`}
            fill={palette.edge}
          />
        </g>
      ) : null}
      <rect
        x={-width / 2 - 0.9}
        y={-height / 2 - 0.9}
        width={width + 1.8}
        height={height + 1.8}
        rx={utility ? 2.5 : 1.8}
        fill="none"
        stroke={GREEN}
        strokeWidth={0.45}
        className="opacity-0 group-focus-visible:opacity-100"
      />
      <rect
        x={-width / 2}
        y={-height / 2}
        width={width}
        height={height}
        rx={utility ? 1.8 : 1.15}
        fill={selected ? "#b5ead7" : palette.top}
        stroke={emphasized ? GREEN : palette.side}
        strokeWidth={emphasized ? 0.65 : 0.25}
        className={perspective ? "motion-safe:transition-colors group-hover:stroke-[#176b52]" : "group-hover:stroke-[#176b52]"}
      />
      {utility ? (
        <UtilitySymbol category={location.category_slug} />
      ) : entrance ? (
        <path d="M-1.5 -2.8h3M0 -3.5v2M-1 -2.5l1 1 1-1" stroke={GREEN} strokeWidth={0.55} fill="none" strokeLinecap="round" />
      ) : (
        <path d={`M ${-width / 2 + 2} ${height / 2 - 0.3} h ${width - 4}`} stroke="#ffffff" strokeWidth={0.7} />
      )}
      <text
        textAnchor="middle"
        fill={INK}
        className="pointer-events-none select-none"
        style={{ fontSize: utility ? 1.9 : entrance ? Math.min(labelSize, 1.9) : labelSize, fontWeight: 600, letterSpacing: -0.025 }}
      >
        {lines.map((line, index) => (
          <tspan x={0} y={utility ? 2.6 : entrance ? 0.8 + index * 2.3 : (lines.length === 1 ? 0 : -1.4) + index * 2.9} key={index}>
            {line}
          </tspan>
        ))}
      </text>
      {!utility && !entrance ? (
        <text y={4.2} textAnchor="middle" fill="#617269" style={{ fontSize: 1.5, fontWeight: 400 }}>
          {location.category_name}
        </text>
      ) : null}
      {isStart || isEnd || stopNumber !== null ? (
        <g transform={`translate(${width / 2 - 0.7} ${-height / 2 + 0.3})`}>
          <circle r={2.1} fill={isEnd ? INK : GREEN} stroke="#fff" strokeWidth={0.55} />
          <text y={0.75} textAnchor="middle" fill="#ffffff" style={{ fontSize: 2, fontWeight: 700 }}>
            {stopNumber ?? (isStart ? "A" : "B")}
          </text>
        </g>
      ) : null}
      </g>
    </g>
  );
}

function tilePalette(category: string): { top: string; side: string; edge: string } {
  switch (category) {
    case "fashion":
      return { top: "#c9efdf", side: "#96cdb7", edge: "#83bda7" };
    case "electronics":
      return { top: "#c9eaf0", side: "#98c9d2", edge: "#85b8c2" };
    case "food":
      return { top: "#ffe0c5", side: "#dfb78f", edge: "#d2a77c" };
    case "services":
    case "entertainment":
      return { top: "#e4ddf6", side: "#bcb0db", edge: "#aa9dcb" };
    case "entrance":
      return { top: "#e6f7ee", side: "#b3d4c7", edge: "#a2c5b7" };
    default:
      return { top: "#ffffff", side: "#c6d8d0", edge: "#b6c9c0" };
  }
}

function UtilitySymbol({ category }: { category: string }) {
  const common = { stroke: "#62756b", strokeWidth: 0.5, fill: "none", strokeLinecap: "round" as const, strokeLinejoin: "round" as const };
  return (
    <g transform="translate(0 -1.15)" aria-hidden>
      {category === "elevator" ? (
        <><rect x={-1.55} y={-1.5} width={3.1} height={3} rx={0.3} {...common} /><path d="M0 -1.5v3M-2.5 0l-.7-.7-.7.7M2.5 0l.7.7.7-.7" {...common} /></>
      ) : category === "stairs" ? (
        <path d="M-2 1.5h1.3V.5h1.3v-1h1.3v-1H3" {...common} />
      ) : category === "escalator" ? (
        <path d="M-2.6 1.4h1.3l2-2.8h1.6M-2.6 2.1h1.7l2-2.8h1.2" {...common} />
      ) : category === "atm" ? (
        <><rect x={-2} y={-1.4} width={4} height={2.8} rx={0.3} {...common} /><circle r={0.6} {...common} /><path d="M-1.5 0h.2M1.3 0h.2" {...common} /></>
      ) : (
        <><circle cx={-1.1} cy={-1.2} r={0.45} fill="#62756b" /><circle cx={1.1} cy={-1.2} r={0.45} fill="#62756b" /><path d="M-1.1 0v1.8M-1.8.3h1.4M.7 0l-.5 1.3H2L1.5 0M1.1 1.3v.6" {...common} /></>
      )}
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
  if (location.category_slug === "escalator") return "Esc.";
  if (location.category_slug === "entrance") return location.slug.includes("parking") ? "Parking" : "Entrance";
  if (location.category_slug === "stairs") return "Stairs";
  return location.name;
}

function wrapLabel(label: string, limit: number): string[] {
  if (label.length <= limit) return [label];
  const words = label.split(/\s+/);
  if (words.length === 1) return [label];
  const breakAt = words.reduce((best, _, i) => {
    if (i === 0) return best;
    return Math.abs(words.slice(0, i).join(" ").length - label.length / 2) <
      Math.abs(words.slice(0, best).join(" ").length - label.length / 2) ? i : best;
  }, 1);
  return [words.slice(0, breakAt).join(" "), words.slice(breakAt).join(" ")];
}
