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
  const name = `${location.name} ${location.slug}`.toLowerCase();
  if (name.includes(q) || name.includes(alias)) return true;
  // Two letters inside "Electronics" is not a useful match.
  if (q.length < 3 && alias === q) return false;
  const details =
    `${location.category_slug} ${location.category_name} ${location.floor_name} ${location.description ?? ""}`.toLowerCase();
  return details.includes(q) || details.includes(alias);
}

export function filterLocations(locations: MapLocation[], query: string, limit = 8): MapLocation[] {
  const q = query.trim().toLowerCase();
  if (q === "") return [];
  const ranked = locations.flatMap((loc) => {
    if (!matchesLocationQuery(loc, query)) return [];
    const name = loc.name.toLowerCase();
    const rank = name.startsWith(q) ? 0 : name.includes(q) ? 1 : 2;
    return [{ loc, rank }];
  });
  ranked.sort((a, b) => a.rank - b.rank || a.loc.name.localeCompare(b.loc.name));
  return ranked.slice(0, limit).map((row) => row.loc);
}
