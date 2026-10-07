import { describe, expect, it } from "vitest";
import {
  continueMessages,
  routeOnFloor,
  toSvg,
  viewBox,
  type Bounds,
} from "@/lib/map-geometry";
import { MAP_FIXTURE, ROUTE_MULTI_FLOOR } from "@/test/fixtures";

const bounds: Bounds = { minX: 0, minY: 0, maxX: 100, maxY: 80 };

describe("toSvg", () => {
  it("flips y so north is at the top of the SVG", () => {
    expect(toSvg(10, 80, bounds)).toEqual({ x: 10, y: 0 });
    expect(toSvg(10, 0, bounds)).toEqual({ x: 10, y: 80 });
  });
});

describe("viewBox", () => {
  it("starts at y=0 after the flip", () => {
    expect(viewBox(bounds)).toBe("0 0 100 80");
  });
});

describe("routeOnFloor", () => {
  it("keeps only the active floor segment and vertical hops", () => {
    const ground = routeOnFloor(MAP_FIXTURE.nodes, MAP_FIXTURE.edges, ROUTE_MULTI_FLOOR, 0);
    expect(ground.segments).toHaveLength(1);
    expect(ground.segments[0]?.points).toEqual([
      { x: 50, y: 0 },
      { x: 50, y: 40 },
    ]);
    expect(ground.hops).toHaveLength(1);
    expect(ground.hops[0]?.kind).toBe("elevator");
    expect(ground.hops[0]?.toLevel).toBe(1);

    const level1 = routeOnFloor(MAP_FIXTURE.nodes, MAP_FIXTURE.edges, ROUTE_MULTI_FLOOR, 1);
    expect(level1.segments[0]?.points).toEqual([
      { x: 50, y: 40 },
      { x: 30, y: 80 },
    ]);
  });
});

describe("continueMessages", () => {
  it("tells the user to continue via elevator", () => {
    const ground = routeOnFloor(MAP_FIXTURE.nodes, MAP_FIXTURE.edges, ROUTE_MULTI_FLOOR, 0);
    const messages = continueMessages(ground.hops, 0, (level) => (level === 1 ? "Level 1" : "Ground Floor"));
    expect(messages).toEqual(["Continue via elevator to Level 1"]);
  });
});
