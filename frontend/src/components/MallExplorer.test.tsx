import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { MallExplorer } from "@/components/MallExplorer";
import { MAP_FIXTURE, ROUTE_MULTI_FLOOR, ROUTE_SAME_FLOOR, ROUTE_WHEELCHAIR } from "@/test/fixtures";

function jsonResponse(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

describe("MallExplorer", () => {
  beforeEach(() => {
    vi.stubGlobal(
      "fetch",
      vi.fn((input: RequestInfo | URL) => {
        const url = String(input);
        if (url.endsWith("/map")) return Promise.resolve(jsonResponse(MAP_FIXTURE));
        return Promise.resolve(jsonResponse({ code: "unexpected", message: "unhandled fetch" }, 500));
      }),
    );
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("selecting origin and destination sends the correct API request", async () => {
    const user = userEvent.setup();
    const fetchMock = vi.mocked(fetch);
    fetchMock.mockImplementation(async (input, _init) => {
      const url = String(input);
      if (url.endsWith("/map")) return jsonResponse(MAP_FIXTURE);
      if (url.endsWith("/navigation/route")) return jsonResponse(ROUTE_SAME_FLOOR);
      return jsonResponse({ code: "unexpected", message: url }, 500);
    });

    render(<MallExplorer />);
    await screen.findByTestId("mall-map");

    await user.selectOptions(screen.getByTestId("from-select"), "loc-entrance");
    await user.selectOptions(screen.getByTestId("to-select"), "loc-nike");
    await user.click(screen.getByTestId("route-submit"));

    await waitFor(() => {
      const routeCalls = fetchMock.mock.calls.filter(([url]) => String(url).includes("/navigation/route"));
      expect(routeCalls.length).toBeGreaterThan(0);
      const body = JSON.parse(String(routeCalls[0]?.[1]?.body)) as Record<string, unknown>;
      expect(body).toEqual({
        from_location_id: "loc-entrance",
        to_location_id: "loc-nike",
        profile: "normal",
        cost_mode: "distance",
      });
    });
    expect(await screen.findByTestId("route-path")).toBeInTheDocument();
    expect(screen.getByTestId("route-summary")).toHaveTextContent("92 m");
    expect(screen.getByTestId("route-summary")).toHaveTextContent("2 min");
  });

  it("sends the wheelchair profile", async () => {
    const user = userEvent.setup();
    const fetchMock = vi.mocked(fetch);
    fetchMock.mockImplementation(async (input) => {
      const url = String(input);
      if (url.endsWith("/map")) return jsonResponse(MAP_FIXTURE);
      if (url.endsWith("/navigation/route")) return jsonResponse(ROUTE_WHEELCHAIR);
      return jsonResponse({ code: "unexpected", message: url }, 500);
    });

    render(<MallExplorer />);
    await screen.findByTestId("mall-map");
    await user.selectOptions(screen.getByTestId("from-select"), "loc-entrance");
    await user.selectOptions(screen.getByTestId("to-select"), "loc-apple");
    await user.click(screen.getByLabelText("Wheelchair"));
    await user.click(screen.getByTestId("route-submit"));

    await waitFor(() => {
      const routeCalls = fetchMock.mock.calls.filter(([url]) => String(url).includes("/navigation/route"));
      const bodies = routeCalls.map(([, init]) => JSON.parse(String(init?.body)) as { profile: string });
      expect(bodies.some((body) => body.profile === "wheelchair")).toBe(true);
    });
  });

  it("displays a no-route error from the backend", async () => {
    const user = userEvent.setup();
    const fetchMock = vi.mocked(fetch);
    fetchMock.mockImplementation(async (input) => {
      const url = String(input);
      if (url.endsWith("/map")) return jsonResponse(MAP_FIXTURE);
      return jsonResponse({ code: "no_accessible_path", message: "no route under profile wheelchair" }, 422);
    });

    render(<MallExplorer />);
    await screen.findByTestId("mall-map");
    await user.selectOptions(screen.getByTestId("from-select"), "loc-entrance");
    await user.selectOptions(screen.getByTestId("to-select"), "loc-nike");
    await user.click(screen.getByTestId("route-submit"));
    expect(await screen.findByTestId("route-error")).toHaveTextContent(/wheelchair-accessible/i);
    expect(screen.queryByTestId("route-path")).not.toBeInTheDocument();
  });

  it("switches floors and shows the next route segment", async () => {
    const user = userEvent.setup();
    const fetchMock = vi.mocked(fetch);
    fetchMock.mockImplementation(async (input) => {
      const url = String(input);
      if (url.endsWith("/map")) return jsonResponse(MAP_FIXTURE);
      return jsonResponse(ROUTE_MULTI_FLOOR);
    });

    render(<MallExplorer />);
    await screen.findByTestId("mall-map");
    await user.selectOptions(screen.getByTestId("from-select"), "loc-entrance");
    await user.selectOptions(screen.getByTestId("to-select"), "loc-apple");
    await user.click(screen.getByTestId("route-submit"));
    expect(await screen.findByTestId("continue-via")).toHaveTextContent("Continue via elevator to Level 1");

    const groundPath = (await screen.findByTestId("route-path")).getAttribute("d");
    await user.click(screen.getByRole("tab", { name: "Level 1" }));
    expect(screen.getByRole("tab", { name: "Level 1" })).toHaveAttribute("aria-selected", "true");
    const levelPath = (await screen.findByTestId("route-path")).getAttribute("d");
    expect(levelPath).not.toEqual(groundPath);
  });

  it("plans several stops and shows the savings", async () => {
    const user = userEvent.setup();
    const fetchMock = vi.mocked(fetch);
    fetchMock.mockImplementation(async (input) => {
      const url = String(input);
      if (url.endsWith("/map")) return jsonResponse(MAP_FIXTURE);
      if (url.endsWith("/navigation/optimize")) {
        return jsonResponse({
          original_order: [],
          optimized_order: [
            {
              location_id: "loc-entrance",
              name: "Main Entrance",
              slug: "main-entrance",
              floor: "Ground Floor",
              floor_level: 0,
              position: 1,
            },
            {
              location_id: "loc-nike",
              name: "Nike",
              slug: "nike",
              floor: "Ground Floor",
              floor_level: 0,
              position: 2,
            },
            {
              location_id: "loc-apple",
              name: "Apple",
              slug: "apple",
              floor: "Level 1",
              floor_level: 1,
              position: 3,
            },
          ],
          original_distance_m: 200,
          optimized_distance_m: 140,
          distance_saved_m: 60,
          distance_saved_percent: 30,
          original_seconds: 240,
          optimized_seconds: 168,
          estimated_time_saved_seconds: 72,
          floor_changes_original: 1,
          floor_changes_optimized: 1,
          algorithm: "held_karp",
          improved: true,
          message: null,
          node_ids: ["node-a", "node-c", "node-b", "node-c", "node-d", "node-e"],
          instructions: ["Walk to Nike", "Take the elevator", "Walk to Apple"],
          floors: [0, 1],
          profile: "normal",
          cost_mode: "distance",
          astar_calls: 6,
          two_opt_moves: 0,
          nearest_neighbor_distance_m: 150,
          nearest_neighbor_2opt_distance_m: 140,
          exact_distance_m: 140,
          nearest_neighbor_gap_percent: 7.1,
          nearest_neighbor_2opt_gap_percent: 0,
          matrix_m: [
            [0, 92, 140],
            [92, 0, 48],
            [140, 48, 0],
          ],
          labels: ["Main Entrance", "Nike", "Apple"],
        });
      }
      return jsonResponse({ code: "unexpected", message: url }, 500);
    });

    render(<MallExplorer />);
    await screen.findByTestId("mall-map");
    await user.click(screen.getByRole("tab", { name: "Plan" }));
    await user.type(screen.getByTestId("tour-search"), "Nike");
    await user.click(screen.getByRole("button", { name: /Nike/ }));
    await user.type(screen.getByTestId("tour-search"), "Apple");
    await user.click(screen.getByRole("button", { name: /Apple/ }));
    expect(screen.getByTestId("tour-stops")).toHaveTextContent("Nike");
    expect(screen.getByTestId("tour-stops")).toHaveTextContent("Apple");
    await user.click(screen.getByTestId("tour-optimize"));

    expect(await screen.findByTestId("tour-savings")).toHaveTextContent("60.0 m");
    expect(screen.getByTestId("tour-savings")).toHaveTextContent("30%");
    expect(screen.getByTestId("tour-order")).toHaveTextContent("1. Main Entrance");
    expect(screen.getByTestId("tour-order")).toHaveTextContent("2. Nike");
    expect(screen.getByTestId("tour-order")).toHaveTextContent("3. Apple");
    expect(await screen.findByTestId("route-path")).toBeInTheDocument();
    await user.click(screen.getByTestId("tour-start-route"));
    expect(screen.getByTestId("route-path")).toBeInTheDocument();
  });

  it("search result focuses the location", async () => {
    const user = userEvent.setup();
    render(<MallExplorer />);
    await screen.findByTestId("mall-map");
    await user.type(screen.getByTestId("location-search"), "Nike");
    const results = await screen.findByTestId("search-results");
    await user.click(within(results).getByRole("button", { name: /Nike/ }));
    expect(screen.getByTestId("location-card")).toHaveTextContent("Nike");
    expect(screen.getByTestId("location-card")).toHaveTextContent("Fashion");
    expect(screen.getByTestId("location-card")).toHaveTextContent("Ground Floor");
  });
});
