import type { MapLocation } from "@/types/map";

const ALIASES: Record<string, string> = {
  bathroom: "restroom",
  bathrooms: "restroom",
  toilet: "restroom",
  toilets: "restroom",
  wc: "restroom",
};

export function matchesLocationQuery(location: MapLocation, query: string): boolean {
  const q = query.trim().toLowerCase();
  if (q === "") return false;
  const alias = ALIASES[q] ?? q;
  const hay =
    `${location.name} ${location.slug} ${location.category_slug} ${location.category_name} ${location.description ?? ""}`.toLowerCase();
  return hay.includes(q) || hay.includes(alias);
}

export function filterLocations(locations: MapLocation[], query: string, limit = 8): MapLocation[] {
  return locations.filter((loc) => matchesLocationQuery(loc, query)).slice(0, limit);
}
