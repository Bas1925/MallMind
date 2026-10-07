"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { AssistantPanel } from "@/components/assistant/AssistantPanel";
import { FloorSelector } from "@/components/map/FloorSelector";
import { MallMap } from "@/components/map/MallMap";
import { LocationCard } from "@/components/navigation/LocationCard";
import { RouteForm } from "@/components/navigation/RouteForm";
import { RouteInstructions } from "@/components/navigation/RouteInstructions";
import { RouteSummary } from "@/components/navigation/RouteSummary";
import { TourPlanner } from "@/components/navigation/TourPlanner";
import { LocationSearch } from "@/components/search/LocationSearch";
import { fetchMallMap, requestRoute } from "@/lib/api";
import { mapErrorMessage, routeErrorMessage } from "@/lib/errors";
import { continueMessages, routeOnFloor } from "@/lib/map-geometry";
import type { AssistantAction } from "@/types/assistant";
import type { MallMapPayload, MapLocation, RouteProfile, RouteResponse } from "@/types/map";
import type { OptimizeResponse } from "@/types/tour";

const MALL_SLUG = "nova-mall";

type MapState =
  | { kind: "loading" }
  | { kind: "error"; message: string }
  | { kind: "ready"; payload: MallMapPayload };

export function MallExplorer() {
  const [mapState, setMapState] = useState<MapState>({ kind: "loading" });
  const [floorLevel, setFloorLevel] = useState(0);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [fromId, setFromId] = useState("");
  const [toId, setToId] = useState("");
  const [profile, setProfile] = useState<RouteProfile>("normal");
  const [route, setRoute] = useState<RouteResponse | null>(null);
  const [routeError, setRouteError] = useState<string | null>(null);
  const [routing, setRouting] = useState(false);
  const [showGraph, setShowGraph] = useState(false);
  const [panelOpen, setPanelOpen] = useState(true);
  const [panelMode, setPanelMode] = useState<"route" | "plan" | "ask">("route");
  const [stops, setStops] = useState<Array<{ id: string; number: number }> | null>(null);

  useEffect(() => {
    const controller = new AbortController();
    (async () => {
      try {
        const payload = await fetchMallMap(MALL_SLUG, controller.signal);
        if (controller.signal.aborted) return;
        setMapState({ kind: "ready", payload });
        const first = payload.floors[0];
        if (first !== undefined) setFloorLevel(first.level);
      } catch (error) {
        if (controller.signal.aborted) return;
        setMapState({ kind: "error", message: mapErrorMessage(error) });
      }
    })();
    return () => controller.abort();
  }, []);

  const payload = mapState.kind === "ready" ? mapState.payload : null;
  const locations = useMemo(() => payload?.locations ?? [], [payload]);
  const selected: MapLocation | undefined = locations.find((loc) => loc.id === selectedId);

  const floorName = useCallback(
    (level: number): string => {
      const floor = payload?.floors.find((f) => f.level === level);
      return floor?.name ?? `Floor ${level}`;
    },
    [payload],
  );

  const routed = useMemo(() => {
    if (payload === null || route === null) return { segments: [], hops: [], messages: [] as string[] };
    const onFloor = routeOnFloor(payload.nodes, payload.edges, route, floorLevel);
    return {
      ...onFloor,
      messages: continueMessages(onFloor.hops, floorLevel, floorName),
    };
  }, [payload, route, floorLevel, floorName]);

  const runRoute = useCallback(
    async (origin: string, dest: string, nextProfile: RouteProfile) => {
      if (origin === "" || dest === "") return;
      setRouting(true);
      setRouteError(null);
      setStops(null);
      try {
        const result = await requestRoute({
          fromLocationId: origin,
          toLocationId: dest,
          profile: nextProfile,
        });
        setRoute(result);
        const originLoc = locations.find((loc) => loc.id === origin);
        if (originLoc !== undefined) setFloorLevel(originLoc.floor_level);
      } catch (error) {
        setRoute(null);
        setRouteError(routeErrorMessage(error));
      } finally {
        setRouting(false);
      }
    },
    [locations],
  );

  const applyTour = (plan: OptimizeResponse): void => {
    const first = plan.optimized_order[0];
    const last = plan.optimized_order[plan.optimized_order.length - 1];
    const nextProfile: RouteProfile =
      plan.profile === "wheelchair" || plan.profile === "avoid_stairs" ? plan.profile : "normal";
    setProfile(nextProfile);
    setStops(plan.optimized_order.map((stop) => ({ id: stop.location_id, number: stop.position })));
    setRoute({
      route: plan.node_ids,
      node_ids: plan.node_ids,
      distance_m: plan.optimized_distance_m,
      estimated_seconds: plan.optimized_seconds,
      floors: plan.floors,
      instructions: plan.instructions,
      algorithm: plan.algorithm,
      nodes_expanded: plan.astar_calls,
      profile: plan.profile,
      from_location: first?.name ?? "",
      to_location: last?.name ?? "",
    });
    setRouteError(null);
    if (first !== undefined) {
      setFromId(first.location_id);
      setFloorLevel(first.floor_level);
    }
    if (last !== undefined) setToId(last.location_id);
  };

  const focusLocation = (id: string): void => {
    const loc = locations.find((item) => item.id === id);
    setSelectedId(id);
    if (loc !== undefined) setFloorLevel(loc.floor_level);
  };

  const applyAssistantAction = (action: AssistantAction): void => {
    if (action.type === "change_floor" && typeof action.floor_level === "number") {
      setFloorLevel(action.floor_level);
    }
    if (action.type === "highlight_location" && typeof action.location_id === "string") {
      focusLocation(action.location_id);
    }
    if (
      action.type === "show_route" &&
      typeof action.from_location_id === "string" &&
      typeof action.to_location_id === "string"
    ) {
      const nextProfile: RouteProfile =
        action.profile === "wheelchair" || action.profile === "avoid_stairs"
          ? action.profile
          : "normal";
      setFromId(action.from_location_id);
      setToId(action.to_location_id);
      setProfile(nextProfile);
      void runRoute(action.from_location_id, action.to_location_id, nextProfile);
    }
  };

  if (mapState.kind === "loading") {
    return (
      <div className="flex h-dvh items-center justify-center bg-stone-100 text-sm text-stone-500">
        Loading NOVA Mall…
      </div>
    );
  }

  if (mapState.kind === "error") {
    return (
      <div className="flex h-dvh flex-col items-center justify-center gap-3 bg-stone-100 px-6 text-center">
        <h1 className="text-lg font-semibold text-stone-900">Map could not load</h1>
        <p data-testid="map-error" className="max-w-md text-sm text-stone-600">
          {mapState.message}
        </p>
      </div>
    );
  }

  const ready = mapState.payload;

  return (
    <div className="flex h-dvh flex-col bg-stone-100 text-stone-900 md:flex-row">
      <section className="relative min-h-0 flex-1">
        <MallMap
          payload={ready}
          floorLevel={floorLevel}
          selectedId={selectedId}
          startId={fromId === "" ? null : fromId}
          endId={toId === "" ? null : toId}
          route={route}
          showGraph={showGraph}
          stops={stops}
          onSelectLocation={(id) => {
            if (id === null) {
              setSelectedId(null);
              return;
            }
            focusLocation(id);
          }}
        />
        <div className="pointer-events-none absolute inset-x-0 top-0 flex flex-col gap-3 p-3 md:p-4">
          <div className="pointer-events-auto flex flex-wrap items-start justify-between gap-2">
            <div>
              <p className="text-[11px] font-medium uppercase tracking-wide text-stone-500">MallMind</p>
              <h1 className="text-lg font-semibold text-stone-900">{ready.mall.name}</h1>
            </div>
            <FloorSelector
              floors={ready.floors}
              activeLevel={floorLevel}
              routeLevels={route?.floors ?? []}
              onChange={setFloorLevel}
            />
          </div>
          {routed.messages.map((message) => (
            <p
              key={message}
              data-testid="continue-via"
              className="pointer-events-auto max-w-md rounded-lg border border-orange-200 bg-orange-50 px-3 py-2 text-sm font-medium text-orange-900"
            >
              {message}
            </p>
          ))}
        </div>
        <label className="pointer-events-auto absolute bottom-3 start-3 flex items-center gap-2 rounded-full border border-stone-200 bg-white/95 px-3 py-1.5 text-xs text-stone-600 shadow-sm">
          <input
            type="checkbox"
            checked={showGraph}
            onChange={(event) => setShowGraph(event.target.checked)}
          />
          Show graph
        </label>
        <button
          type="button"
          className="absolute bottom-3 end-3 rounded-full border border-stone-200 bg-white px-3 py-1.5 text-xs font-medium text-stone-700 shadow-sm md:hidden"
          onClick={() => setPanelOpen((open) => !open)}
        >
          {panelOpen ? "Hide panel" : "Route & search"}
        </button>
      </section>

      <aside
        className={
          panelOpen
            ? "flex max-h-[48vh] flex-col overflow-hidden border-t border-stone-200 bg-white md:max-h-none md:w-[22.5rem] md:border-s md:border-t-0"
            : "hidden md:flex md:w-[22.5rem] md:flex-col md:overflow-hidden md:border-s md:border-stone-200 md:bg-white"
        }
      >
        <div className="flex-1 space-y-4 overflow-y-auto p-4">
          <LocationSearch locations={locations} onPick={focusLocation} />
          <div className="flex gap-1" role="tablist" aria-label="Panel">
            <button
              type="button"
              role="tab"
              aria-selected={panelMode === "route"}
              className={
                panelMode === "route"
                  ? "rounded-full bg-stone-900 px-3 py-1 text-xs font-semibold text-white"
                  : "rounded-full border border-stone-200 px-3 py-1 text-xs text-stone-600"
              }
              onClick={() => setPanelMode("route")}
            >
              Route
            </button>
            <button
              type="button"
              role="tab"
              aria-selected={panelMode === "plan"}
              className={
                panelMode === "plan"
                  ? "rounded-full bg-stone-900 px-3 py-1 text-xs font-semibold text-white"
                  : "rounded-full border border-stone-200 px-3 py-1 text-xs text-stone-600"
              }
              onClick={() => setPanelMode("plan")}
            >
              Plan
            </button>
            <button
              type="button"
              role="tab"
              aria-selected={panelMode === "ask"}
              className={
                panelMode === "ask"
                  ? "rounded-full bg-stone-900 px-3 py-1 text-xs font-semibold text-white"
                  : "rounded-full border border-stone-200 px-3 py-1 text-xs text-stone-600"
              }
              onClick={() => setPanelMode("ask")}
            >
              Ask
            </button>
          </div>
          {panelMode === "ask" ? (
            <AssistantPanel
              profile={profile}
              currentLocationId={fromId === "" ? null : fromId}
              onAction={(action) => applyAssistantAction(action)}
            />
          ) : panelMode === "plan" ? (
            <TourPlanner
              locations={locations}
              profile={profile}
              onProfile={setProfile}
              onApply={applyTour}
            />
          ) : (
            <RouteForm
            locations={locations}
            fromId={fromId}
            toId={toId}
            profile={profile}
            loading={routing}
            onFrom={setFromId}
            onTo={setToId}
            onProfile={(next) => {
              setProfile(next);
              if (fromId !== "" && toId !== "") {
                void runRoute(fromId, toId, next);
              }
            }}
            onSubmit={() => {
              void runRoute(fromId, toId, profile);
            }}
            onSwap={() => {
              setFromId(toId);
              setToId(fromId);
            }}
          />
          )}
          {routeError !== null ? (
            <p
              data-testid="route-error"
              className="rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-800"
            >
              {routeError}
            </p>
          ) : null}
          {selected !== undefined ? (
            <LocationCard
              location={selected}
              onNavigate={() => {
                setToId(selected.id);
                if (fromId !== "") void runRoute(fromId, selected.id, profile);
              }}
              onSetStart={() => setFromId(selected.id)}
            />
          ) : null}
          {route !== null ? (
            <>
              <RouteSummary route={route} floorName={floorName} />
              <RouteInstructions instructions={route.instructions} />
            </>
          ) : (
            <p className="text-xs text-stone-500">
              Routes come from the backend A* API. The map only draws what the server returns.
            </p>
          )}
        </div>
      </aside>
    </div>
  );
}
