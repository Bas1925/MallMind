import { act, render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { MallExplorer } from "@/components/MallExplorer";
import { MAP_FIXTURE, ROUTE_MULTI_FLOOR, ROUTE_SAME_FLOOR, ROUTE_WHEELCHAIR } from "@/test/fixtures";

async function pickPlace(
  user: ReturnType<typeof userEvent.setup>,
  testId: string,
  typed: string,
  optionName: RegExp,
): Promise<void> {
  const field = screen.getByTestId(testId);
  await user.click(field);
  await user.type(field, typed);
  const list = await screen.findByTestId(`${testId}-results`);
  await user.click(within(list).getByRole("option", { name: optionName }));
}

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

  it("provides bounded map zoom without changing the selected floor or view", async () => {
    const user = userEvent.setup();
    render(<MallExplorer initialView="map" />);
    await screen.findByTestId("mall-map");
    await user.click(screen.getByRole("tab", { name: "Level 1" }));

    const zoomIn = screen.getByRole("button", { name: "Zoom in" });
    const zoomOut = screen.getByRole("button", { name: "Zoom out" });
    const zoom = screen.getByRole("status", { name: "Map zoom" });
    expect(zoomOut).toBeDisabled();
    expect(zoom).toHaveTextContent("1×");
    await user.click(zoomIn);
    expect(zoom).toHaveTextContent("1.5×");
    await user.click(zoomIn);
    expect(zoom).toHaveTextContent("2×");
    expect(zoomIn).toBeDisabled();
    expect(screen.getByRole("region", { name: "Mall map viewport" })).toHaveAttribute("tabindex", "0");
    expect(screen.getByRole("tab", { name: "Level 1" })).toHaveAttribute("aria-selected", "true");
    expect(screen.getByRole("button", { name: "3D view" })).toHaveAttribute("aria-pressed", "true");
    await user.click(screen.getByRole("button", { name: "2D" }));
    expect(zoom).toHaveTextContent("2×");
    await user.click(zoomOut);
    await user.click(zoomOut);
    expect(zoom).toHaveTextContent("1×");
    expect(zoomOut).toBeDisabled();
  });

  it("moves keyboard focus into the visit panel after a shortcut", async () => {
    const user = userEvent.setup();
    vi.stubGlobal("matchMedia", vi.fn(() => ({ matches: true })));
    render(<MallExplorer initialView="map" />);
    await screen.findByTestId("mall-map");
    const panel = screen.getByRole("complementary", { name: "Plan your visit" });
    panel.scrollIntoView = vi.fn();

    await user.click(screen.getByRole("button", { name: /More stops, less walking/ }));

    expect(panel).toHaveFocus();
    expect(panel.scrollIntoView).toHaveBeenCalledWith({ behavior: "instant", block: "start" });
    await user.tab();
    expect(screen.getByTestId("location-search")).toHaveFocus();
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

    render(<MallExplorer initialView="map" />);
    await screen.findByTestId("mall-map");

    await pickPlace(user, "from-select", "Main", /Main Entrance/);
    await pickPlace(user, "to-select", "Nike", /Nike/);
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
        algorithm: "astar",
      });
    });
    expect(await screen.findByTestId("route-path")).toBeInTheDocument();
    expect(screen.getByTestId("route-summary")).toHaveTextContent("92 m");
    expect(screen.getByTestId("route-summary")).toHaveTextContent("2 min");
    await user.click(screen.getByRole("button", { name: "2D" }));
    expect(screen.getByRole("button", { name: "2D" })).toHaveAttribute("aria-pressed", "true");
    expect(screen.getByTestId("route-path")).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "3D view" }));
    expect(screen.getByTestId("route-summary")).toHaveTextContent("92 m");
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

    render(<MallExplorer initialView="map" />);
    await screen.findByTestId("mall-map");
    await pickPlace(user, "from-select", "Main", /Main Entrance/);
    await pickPlace(user, "to-select", "Apple", /Apple/);
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

    render(<MallExplorer initialView="map" />);
    await screen.findByTestId("mall-map");
    await pickPlace(user, "from-select", "Main", /Main Entrance/);
    await pickPlace(user, "to-select", "Nike", /Nike/);
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

    render(<MallExplorer initialView="map" />);
    await screen.findByTestId("mall-map");
    await pickPlace(user, "from-select", "Main", /Main Entrance/);
    await pickPlace(user, "to-select", "Apple", /Apple/);
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

    render(<MallExplorer initialView="map" />);
    await screen.findByTestId("mall-map");
    await user.click(screen.getByRole("tab", { name: "Plan" }));
    await user.type(screen.getByTestId("tour-search"), "Nike");
    await user.click(within(screen.getByRole("tabpanel")).getByRole("button", { name: /Nike/ }));
    await user.type(screen.getByTestId("tour-search"), "Apple");
    await user.click(within(screen.getByRole("tabpanel")).getByRole("button", { name: /Apple/ }));
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
    render(<MallExplorer initialView="map" />);
    await screen.findByTestId("mall-map");
    await user.type(screen.getByTestId("location-search"), "Nike");
    const results = await screen.findByTestId("search-results");
    await user.click(within(results).getByRole("option", { name: /Nike/ }));
    expect(screen.getByTestId("location-card")).toHaveTextContent("Nike");
    expect(screen.getByTestId("location-card")).toHaveTextContent("Fashion");
    expect(screen.getByTestId("location-card")).toHaveTextContent("Ground Floor");
  });

  it("recovers from a transient map-loading failure", async () => {
    const user = userEvent.setup();
    const fetchMock = vi.mocked(fetch);
    fetchMock
      .mockRejectedValueOnce(new TypeError("network unavailable"))
      .mockResolvedValueOnce(jsonResponse(MAP_FIXTURE));

    render(<MallExplorer initialView="map" />);
    expect(await screen.findByTestId("map-error")).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "Try again" }));
    expect(await screen.findByTestId("mall-map")).toBeInTheDocument();
    expect(fetchMock).toHaveBeenCalledTimes(2);
  });

  it("ignores a late route after the destination changes", async () => {
    const user = userEvent.setup();
    let finish: ((response: Response) => void) | undefined;
    let signal: AbortSignal | null | undefined;
    vi.mocked(fetch).mockImplementation(async (input, init) => {
      if (String(input).endsWith("/map")) return jsonResponse(MAP_FIXTURE);
      signal = init?.signal;
      return new Promise<Response>((resolve) => { finish = resolve; });
    });
    render(<MallExplorer initialView="map" />);
    await screen.findByTestId("mall-map");
    await pickPlace(user, "from-select", "Main", /Main Entrance/);
    await pickPlace(user, "to-select", "Nike", /Nike/);
    await user.click(screen.getByTestId("route-submit"));
    await pickPlace(user, "to-select", "Apple", /Apple/);
    expect(signal?.aborted).toBe(true);
    await act(async () => { finish?.(jsonResponse(ROUTE_SAME_FLOOR)); });
    expect(screen.queryByTestId("route-summary")).not.toBeInTheDocument();
    expect(screen.getByTestId("to-select")).toHaveValue("Apple · Level 1");
    expect(screen.getByTestId("route-submit")).toBeEnabled();
  });

  it("clears an existing route when endpoints are swapped", async () => {
    const user = userEvent.setup();
    vi.mocked(fetch).mockImplementation(async (input) =>
      jsonResponse(String(input).endsWith("/map") ? MAP_FIXTURE : ROUTE_SAME_FLOOR));
    render(<MallExplorer initialView="map" />);
    await screen.findByTestId("mall-map");
    await pickPlace(user, "from-select", "Main", /Main Entrance/);
    await pickPlace(user, "to-select", "Nike", /Nike/);
    await user.click(screen.getByTestId("route-submit"));
    await screen.findByTestId("route-summary");
    await user.click(screen.getByRole("button", { name: /swap/i }));
    expect(screen.queryByTestId("route-summary")).not.toBeInTheDocument();
    expect(screen.getByTestId("from-select")).toHaveValue("Nike · Ground Floor");
  });
});
