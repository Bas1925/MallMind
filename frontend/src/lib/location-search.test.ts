import { describe, expect, it } from "vitest";
import { filterLocations, matchesLocationQuery } from "@/lib/location-search";
import { MAP_FIXTURE } from "@/test/fixtures";

describe("location search", () => {
  it("matches store names", () => {
    const nike = MAP_FIXTURE.locations.find((loc) => loc.slug === "nike");
    expect(nike).toBeDefined();
    if (nike === undefined) return;
    expect(matchesLocationQuery(nike, "Nike")).toBe(true);
  });

  it("aliases bathroom to restroom category", () => {
    const restroom = MAP_FIXTURE.locations[0];
    expect(restroom).toBeDefined();
    if (restroom === undefined) return;
    expect(
      matchesLocationQuery(
        {
          ...restroom,
          slug: "restroom-g",
          name: "Restroom — Ground",
          category_slug: "restroom",
          category_name: "Restroom",
        },
        "bathroom",
      ),
    ).toBe(true);
  });

  it("keeps a two-letter query on the place name", () => {
    const hits = filterLocations(MAP_FIXTURE.locations, "ni");
    expect(hits.map((loc) => loc.name)).toEqual(["Nike"]);
  });

  it("returns name, category, and floor in filtered results", () => {
    const hits = filterLocations(MAP_FIXTURE.locations, "nike");
    expect(hits).toHaveLength(1);
    expect(hits[0]?.name).toBe("Nike");
    expect(hits[0]?.category_name).toBe("Fashion");
    expect(hits[0]?.floor_name).toBe("Ground Floor");
  });
});
