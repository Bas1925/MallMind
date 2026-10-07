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
import { Icon } from "@/components/ui/Icon";
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
      <div className="flex h-dvh flex-col items-center justify-center gap-4 bg-ink-950">
        <BrandMark />
        <div className="h-0.5 w-32 overflow-hidden rounded-full bg-white/[0.06]">
          <div className="h-full w-1/3 animate-[route-flow_1s_linear_infinite] rounded-full bg-gold-400" />
        </div>
        <p className="text-xs tracking-wide text-mist-500">Loading NOVA Mall…</p>
      </div>
    );
  }

  if (mapState.kind === "error") {
    return (
      <div className="flex h-dvh flex-col items-center justify-center gap-3 bg-ink-950 px-6 text-center">
        <BrandMark />
        <h1 className="mt-4 font-display text-3xl text-mist-50">Map could not load</h1>
        <p data-testid="map-error" className="max-w-md text-sm text-mist-400">
          {mapState.message}
        </p>
      </div>
    );
  }

  const ready = mapState.payload;
  const tabs = [
    { id: "route", label: "Route", icon: "route" },
    { id: "plan", label: "Plan", icon: "list" },
    { id: "ask", label: "Ask", icon: "sparkle" },
  ] as const;

  return (
    <div className="relative flex h-dvh flex-col overflow-hidden bg-ink-950 text-mist-50 md:flex-row">
      {/* Ambient light behind the map. */}
      <div
        className="pointer-events-none absolute inset-0 bg-[radial-gradient(ellipse_at_30%_20%,rgba(232,184,106,0.10),transparent_55%),radial-gradient(ellipse_at_80%_90%,rgba(94,200,255,0.06),transparent_50%)]"
        aria-hidden
      />

      <section className="relative min-h-0 flex-1">
        <div className="absolute inset-0 px-1 pb-12 pt-[7.25rem] sm:pt-24 md:px-10 md:pb-14">
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
        </div>

        <header className="pointer-events-none absolute inset-x-0 top-0 flex flex-wrap items-start justify-between gap-3 p-3 md:p-5">
          <div className="pointer-events-auto flex items-center gap-3">
            <BrandMark />
            <div className="leading-tight">
              <p className="eyebrow">MallMind</p>
              <h1 className="font-display text-2xl text-mist-50">{ready.mall.name}</h1>
            </div>
          </div>
          <div className="pointer-events-auto">
            <FloorSelector
              floors={ready.floors}
              activeLevel={floorLevel}
              routeLevels={route?.floors ?? []}
              onChange={setFloorLevel}
            />
          </div>
        </header>

        <div className="pointer-events-none absolute inset-x-0 bottom-3 flex flex-col items-start gap-1.5 pe-36 ps-3 md:bottom-5 md:items-center md:px-3">
          {routed.messages.map((message) => (
            <p
              key={message}
              data-testid="continue-via"
              className="glass rise pointer-events-auto flex items-center gap-2 rounded-full px-3 py-1.5 text-[11px] font-medium text-gold-200 md:px-3.5 md:text-xs"
            >
              <Icon name="elevator" size={14} />
              {message}
            </p>
          ))}
        </div>

        <label className="glass pointer-events-auto absolute bottom-3 start-3 hidden cursor-pointer items-center gap-2 rounded-full px-3 py-1.5 text-xs text-mist-400 transition hover:text-mist-50 md:bottom-5 md:start-5 md:flex">
          <input
            type="checkbox"
            checked={showGraph}
            onChange={(event) => setShowGraph(event.target.checked)}
            className="accent-gold-400"
          />
          <Icon name="layers" size={13} />
          Show graph
        </label>
        <button
          type="button"
          className="glass absolute bottom-3 end-3 rounded-full px-3.5 py-1.5 text-xs font-semibold text-mist-50 md:hidden"
          onClick={() => setPanelOpen((open) => !open)}
        >
          {panelOpen ? "Hide panel" : "Route & search"}
        </button>
      </section>

      <aside
        className={`${
          panelOpen ? "flex" : "hidden md:flex"
        } glass relative z-10 max-h-[52vh] flex-col overflow-hidden rounded-t-3xl md:m-4 md:max-h-none md:w-[24rem] md:rounded-3xl`}
      >
        <div className="mx-auto mt-2 h-1 w-10 rounded-full bg-white/15 md:hidden" aria-hidden />
        <div className="space-y-4 border-b border-white/[0.06] p-4 pb-3">
          <LocationSearch locations={locations} onPick={focusLocation} />
          <div className="grid grid-cols-3 gap-1 rounded-xl bg-ink-950/60 p-1" role="tablist" aria-label="Panel">
            {tabs.map((tab) => (
              <button
                key={tab.id}
                type="button"
                role="tab"
                aria-selected={panelMode === tab.id}
                className={`flex items-center justify-center gap-1.5 rounded-lg py-1.5 text-xs font-semibold transition ${
                  panelMode === tab.id
                    ? "bg-ink-700 text-mist-50 shadow"
                    : "text-mist-500 hover:text-mist-200"
                }`}
                onClick={() => setPanelMode(tab.id)}
              >
                <Icon name={tab.icon} size={13} />
                {tab.label}
              </button>
            ))}
          </div>
        </div>

        <div className="scroll-thin flex-1 space-y-4 overflow-y-auto p-4">
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
              className="rounded-xl border border-rose-400/30 bg-rose-400/10 px-3 py-2 text-sm text-rose-400"
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
          ) : panelMode === "route" ? (
            <p className="px-1 text-[11px] leading-relaxed text-mist-500">
              Every route is computed by the backend A* engine. The map only draws what the server
              returns.
            </p>
          ) : null}
        </div>
      </aside>
    </div>
  );
}

function BrandMark() {
  return (
    <span className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-gold-200 via-gold-400 to-gold-500 shadow-glow">
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" aria-hidden>
        <path
          d="M4 19V6.5l8 7 8-7V19"
          stroke="#07090d"
          strokeWidth={2.4}
          strokeLinecap="round"
          strokeLinejoin="round"
        />
      </svg>
    </span>
  );
}
