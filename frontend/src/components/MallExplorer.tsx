"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { AssistantPanel } from "@/components/assistant/AssistantPanel";
import { StoreDirectory } from "@/components/directory/StoreDirectory";
import { StoreMark } from "@/components/directory/StoreMark";
import { StoreBrand, STORE_BRANDS } from "@/components/directory/StoreBrand";
import { FloorSelector } from "@/components/map/FloorSelector";
import { MallMap } from "@/components/map/MallMap";
import { LocationCard } from "@/components/navigation/LocationCard";
import { RouteForm } from "@/components/navigation/RouteForm";
import { RouteInstructions } from "@/components/navigation/RouteInstructions";
import { RouteSummary } from "@/components/navigation/RouteSummary";
import { TourPlanner } from "@/components/navigation/TourPlanner";
import { ParkingPanel } from "@/components/parking/ParkingPanel";
import { LocationSearch } from "@/components/search/LocationSearch";
import { Icon } from "@/components/ui/Icon";
import { fetchMallMap, requestRoute } from "@/lib/api";
import { mapErrorMessage, routeErrorMessage } from "@/lib/errors";
import { continueMessages, routeOnFloor } from "@/lib/map-geometry";
import type { AssistantAction } from "@/types/assistant";
import type { MallMapPayload, MapLocation, RouteProfile, RouteResponse, SearchAlgorithm } from "@/types/map";
import type { OptimizeResponse } from "@/types/tour";

const MALL_SLUG = "nova-mall";

type MapState =
  | { kind: "loading" }
  | { kind: "error"; message: string }
  | { kind: "ready"; payload: MallMapPayload };

export function MallExplorer({ initialView = "stores" }: { initialView?: "stores" | "map" }) {
  const [view, setView] = useState<"stores" | "map">(initialView);
  const [visitIds, setVisitIds] = useState<string[]>([]);
  const [mapState, setMapState] = useState<MapState>({ kind: "loading" });
  const [mapRequest, setMapRequest] = useState(0);
  const [floorLevel, setFloorLevel] = useState(0);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [fromId, setFromId] = useState("");
  const [toId, setToId] = useState("");
  const [profile, setProfile] = useState<RouteProfile>("normal");
  const [algorithm, setAlgorithm] = useState<SearchAlgorithm>("astar");
  const [traceLimit, setTraceLimit] = useState<number | null>(null);
  const [route, setRoute] = useState<RouteResponse | null>(null);
  const [routeError, setRouteError] = useState<string | null>(null);
  const [routing, setRouting] = useState(false);
  const [showGraph, setShowGraph] = useState(false);
  const [perspective, setPerspective] = useState(true);
  const [mapZoom, setMapZoom] = useState(1);
  const panelRef = useRef<HTMLElement>(null);
  const [panelMode, setPanelMode] = useState<"route" | "plan" | "ask" | "parking">("route");
  const [stops, setStops] = useState<Array<{ id: string; number: number }> | null>(null);
  const routeRequest = useRef<AbortController | null>(null);

  useEffect(() => {
    const syncView = () => {
      const hash = window.location.hash;
      setView(hash === "#map" || hash === "#plan" ? "map" : hash === "#stores" ? "stores" : initialView);
      if (hash === "#plan") setPanelMode("plan");
    };
    syncView();
    window.addEventListener("hashchange", syncView);
    window.addEventListener("popstate", syncView);
    return () => {
      window.removeEventListener("hashchange", syncView);
      window.removeEventListener("popstate", syncView);
    };
  }, [initialView]);

  const openView = (next: "stores" | "map" | "plan") => {
    setView(next === "stores" ? "stores" : "map");
    if (next === "plan") setPanelMode("plan");
    if (next === "map") setPanelMode("route");
    const hash = `#${next}`;
    if (window.location.hash !== hash) window.history.pushState(null, "", hash);
    requestAnimationFrame(() => {
      document.getElementById(next === "stores" ? "store-directory" : "visit-panel")?.focus({ preventScroll: true });
      window.scrollTo({ top: 0, behavior: "instant" });
    });
  };

  const clearRoute = useCallback(() => {
    routeRequest.current?.abort();
    routeRequest.current = null;
    setRouting(false);
    setRoute(null);
    setRouteError(null);
    setStops(null);
  }, []);

  useEffect(() => () => routeRequest.current?.abort(), []);

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
  }, [mapRequest]);

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
    async (
      origin: string,
      dest: string,
      nextProfile: RouteProfile,
      nextAlgorithm: SearchAlgorithm = algorithm,
    ) => {
      if (origin === "" || dest === "") return;
      routeRequest.current?.abort();
      const controller = new AbortController();
      routeRequest.current = controller;
      setRouting(true);
      setRoute(null);
      setRouteError(null);
      setStops(null);
      setTraceLimit(null);
      try {
        const result = await requestRoute({
          fromLocationId: origin,
          toLocationId: dest,
          profile: nextProfile,
          algorithm: nextAlgorithm,
        }, controller.signal);
        if (controller.signal.aborted) return;
        setRoute(result);
        const originLoc = locations.find((loc) => loc.id === origin);
        if (originLoc !== undefined) setFloorLevel(originLoc.floor_level);
      } catch (error) {
        if (controller.signal.aborted) return;
        setRoute(null);
        setRouteError(routeErrorMessage(error));
      } finally {
        if (routeRequest.current === controller) setRouting(false);
      }
    },
    [locations, algorithm],
  );

  const openSearchMaze = useCallback(() => {
    const start = locations.find((loc) => loc.slug === "search-start");
    const goal = locations.find((loc) => loc.slug === "search-goal");
    if (start === undefined || goal === undefined) return;
    setAlgorithm("bfs");
    setProfile("normal");
    setFromId(start.id);
    setToId(goal.id);
    setFloorLevel(start.floor_level);
    setPerspective(false);
    setSelectedId(goal.id);
    setTraceLimit(null);
    void runRoute(start.id, goal.id, "normal", "bfs");
  }, [locations, runRoute]);

  const applyTour = (plan: OptimizeResponse): void => {
    clearRoute();
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
        <div className="h-0.5 w-32 overflow-hidden rounded-full bg-ink-600">
          <div className="loading-progress h-full w-1/3 rounded-full bg-gold-400" />
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
        <button
          type="button"
          className="btn-primary mt-2 w-auto px-6"
          onClick={() => {
            setMapState({ kind: "loading" });
            setMapRequest((request) => request + 1);
          }}
        >
          Try again
        </button>
      </div>
    );
  }

  const ready = mapState.payload;
  const tabs = [
    { id: "route", label: "Route", icon: "route" },
    { id: "plan", label: "Plan", icon: "list" },
    { id: "ask", label: "Ask", icon: "sparkle" },
    { id: "parking", label: "Park", icon: "car" },
  ] as const;

  const floorLocations = locations.filter(
    (location) => location.floor_level === floorLevel && location.node_type === "store_anchor",
  );
  const scrollToPanel = (): void => {
    panelRef.current?.focus({ preventScroll: true });
    panelRef.current?.scrollIntoView({
      behavior: window.matchMedia("(prefers-reduced-motion: reduce)").matches ? "instant" : "smooth",
      block: "start",
    });
  };

  return (
    <div className="app-shell">
      <a className="skip-link" href={view === "stores" ? "#store-directory" : "#visit-panel"}>Skip to content</a>
      <header className="app-header discovery-header">
        <button type="button" className="app-brand" aria-label="MallMind home" onClick={() => openView("stores")}>
          <BrandMark />
          <div>
            <p className="brand-name">mallmind<span className="text-gold-400">.</span></p>
            <p className="brand-subtitle">A better way around.</p>
          </div>
        </button>
        <nav className="discovery-nav" aria-label="Main navigation">
          <button type="button" aria-current={view === "stores" ? "page" : undefined} onClick={() => openView("stores")}>Stores & dining</button>
          <button type="button" aria-current={view === "map" && panelMode !== "plan" ? "page" : undefined} onClick={() => openView("map")}>Mall map</button>
          <button type="button" aria-current={view === "map" && panelMode === "plan" ? "page" : undefined} onClick={() => openView("plan")}>My visit <span>{visitIds.length}</span></button>
        </nav>
        <div className="discovery-location">
          <Icon name="pin" size={15} /><strong>{ready.mall.name}</strong><span>DEMO</span>
        </div>
      </header>

      <div hidden={view !== "stores"}>
        <StoreDirectory
          active={view === "stores"}
          locations={locations}
          floors={ready.floors}
          visitIds={visitIds}
          onToggleVisit={(id) => {
            clearRoute();
            setVisitIds((ids) => ids.includes(id) ? ids.filter((item) => item !== id) : [...ids, id]);
          }}
          onOpenLocation={(id, navigate) => {
            clearRoute();
            focusLocation(id);
            openView("map");
            if (navigate) {
              const origin = fromId || locations.find((loc) => loc.slug === "main-entrance")?.id || "";
              setFromId(origin);
              setToId(id);
              if (origin !== "") void runRoute(origin, id, profile);
            }
          }}
          onPlan={() => openView("plan")}
          onMap={() => openView("map")}
        />
      </div>
      <div hidden={view !== "map"}>
      <main className="workspace">
        <aside ref={panelRef} id="visit-panel" className="explorer-panel" aria-label="Plan your visit" tabIndex={-1}>
          <div className="panel-intro">
            <p className="eyebrow">Directions</p>
            <h1>Where to?</h1>
            <p>Pick a start and a destination. Then choose how you walk and how the search works.</p>
          </div>
          <div className="panel-search">
            <LocationSearch locations={locations} onPick={focusLocation} />
          </div>
          <div className="panel-tabs" role="tablist" aria-label="Panel">
            {tabs.map((tab, index) => (
              <button
                key={tab.id}
                id={`panel-tab-${tab.id}`}
                type="button"
                role="tab"
                aria-controls="panel-content"
                aria-selected={panelMode === tab.id}
                tabIndex={panelMode === tab.id ? 0 : -1}
                className="panel-tab"
                onClick={() => setPanelMode(tab.id)}
                onKeyDown={(event) => {
                  let nextIndex: number;
                  if (event.key === "ArrowRight") nextIndex = (index + 1) % tabs.length;
                  else if (event.key === "ArrowLeft") nextIndex = (index + tabs.length - 1) % tabs.length;
                  else if (event.key === "Home") nextIndex = 0;
                  else if (event.key === "End") nextIndex = tabs.length - 1;
                  else return;
                  event.preventDefault();
                  const nextTab = tabs[nextIndex];
                  if (nextTab !== undefined) {
                    setPanelMode(nextTab.id);
                    document.getElementById(`panel-tab-${nextTab.id}`)?.focus();
                  }
                }}
              >
                <Icon name={tab.icon} size={15} />
                {tab.label}
              </button>
            ))}
          </div>

          <div className="panel-content" id="panel-content" role="tabpanel" aria-labelledby={`panel-tab-${panelMode}`}>
            {panelMode === "parking" ? (
              <ParkingPanel
                mallSlug={ready.mall.slug}
                locations={locations}
                hasRouteOrigin={fromId !== ""}
                onNavigate={(entranceLocationId) => {
                  clearRoute();
                  focusLocation(entranceLocationId);
                  setToId(entranceLocationId);
                  setPanelMode("route");
                  if (fromId !== "" && fromId !== entranceLocationId) {
                    void runRoute(fromId, entranceLocationId, profile);
                  }
                }}
              />
            ) : panelMode === "ask" ? (
              <AssistantPanel
                profile={profile}
                currentLocationId={fromId === "" ? null : fromId}
                onAction={(action) => applyAssistantAction(action)}
              />
            ) : panelMode === "plan" ? (
              <TourPlanner
                locations={locations}
                profile={profile}
                onProfile={(next) => { clearRoute(); setProfile(next); }}
                onInvalidate={clearRoute}
                onApply={applyTour}
                stopIds={visitIds}
                onStopIdsChange={setVisitIds}
              />
            ) : (
              <>
                <div>
                  <h2 className="panel-heading">Get directions</h2>
                  <p className="panel-subheading">Start, destination, how you walk, then how to search.</p>
                </div>
                <RouteForm
                  locations={locations}
                  fromId={fromId}
                  toId={toId}
                  profile={profile}
                  algorithm={algorithm}
                  loading={routing}
                  onFrom={(id) => { clearRoute(); setFromId(id); }}
                  onTo={(id) => { clearRoute(); setToId(id); }}
                  onProfile={(next) => {
                    setProfile(next);
                    if (fromId !== "" && toId !== "") void runRoute(fromId, toId, next, algorithm);
                  }}
                  onAlgorithm={(next) => {
                    setAlgorithm(next);
                    setTraceLimit(null);
                    if (fromId !== "" && toId !== "") void runRoute(fromId, toId, profile, next);
                  }}
                  onMazeExample={() => openSearchMaze()}
                  onSubmit={() => void runRoute(fromId, toId, profile, algorithm)}
                  onSwap={() => {
                    clearRoute();
                    setFromId(toId);
                    setToId(fromId);
                  }}
                />
              </>
            )}
            {routeError !== null ? (
              <p data-testid="route-error" role="alert" className="rounded-xl border border-rose-400/30 bg-rose-400/5 px-3 py-2 text-sm text-rose-400">
                {routeError}
              </p>
            ) : null}
            {selected !== undefined ? (
              <LocationCard
                location={selected}
                onNavigate={() => {
                  clearRoute();
                  setToId(selected.id);
                  setPanelMode("route");
                  if (fromId !== "") void runRoute(fromId, selected.id, profile);
                }}
                onSetStart={() => {
                  clearRoute();
                  setFromId(selected.id);
                  setPanelMode("route");
                }}
              />
            ) : null}
            {route !== null ? (
              <>
                <RouteSummary route={route} floorName={floorName} onTrace={setTraceLimit} />
                <RouteInstructions instructions={route.instructions} />
                <button type="button" className="btn-ghost" onClick={clearRoute}>Clear route</button>
              </>
            ) : panelMode === "route" ? (
              <p className="route-empty">
                <Icon name="pin" size={15} />
                Tap a place on the map to see details or use it as your starting point.
              </p>
            ) : null}
            {panelMode === "route" && selected === undefined && route === null && floorLocations.length > 0 ? (
              <section className="floor-directory" aria-label="Explore this floor">
                <div className="flex items-center justify-between gap-3">
                  <h2 className="text-xs font-semibold">On this floor</h2>
                  <span className="text-[10px] text-mist-500">{floorLocations.length} places</span>
                </div>
                {floorLocations.slice(0, 3).map((location) => (
                  <button type="button" className="directory-row" key={location.id} onClick={() => focusLocation(location.id)}>
                    <span className="directory-avatar" aria-hidden>{STORE_BRANDS[location.slug] ? <StoreBrand slug={location.slug} name={location.name} /> : <StoreMark slug={location.slug} name={location.name} size={36} />}</span>
                    <span className="flex-1">
                      <span className="directory-name">{location.name}</span>
                      <span className="directory-category">{location.category_name}</span>
                    </span>
                    <Icon name="send" size={13} className="text-mist-500" />
                  </button>
                ))}
              </section>
            ) : null}
          </div>
        </aside>

        <section className="map-workspace" aria-labelledby="map-title">
          <div className="map-heading">
            <div>
              <p className="eyebrow"><Icon name="layers" size={12} /> EXPLORE THE MALL</p>
              <h2 id="map-title">A place for every stop.</h2>
            </div>
            <FloorSelector
              floors={ready.floors}
              activeLevel={floorLevel}
              routeLevels={route?.floors ?? []}
              onChange={setFloorLevel}
            />
          </div>

          <div className="map-card">
            <div className="map-card-toolbar">
              <span className="map-floor-label">{floorName(floorLevel)}</span>
              <div className="map-view-controls" role="group" aria-label="Map view">
                <button type="button" aria-pressed={!perspective} onClick={() => setPerspective(false)}>2D</button>
                <button type="button" aria-pressed={perspective} onClick={() => setPerspective(true)}><Icon name="layers" size={13} /> 3D view</button>
              </div>
            </div>
            <div className={`map-canvas ${perspective ? "map-perspective" : "map-flat"} ${mapZoom > 1 ? "map-zoomed" : ""}`}>
              <div className="map-compass" aria-hidden="true"><span>N</span><Icon name="up" size={17} /></div>
              <div className="map-scene" role="region" aria-label="Mall map viewport" tabIndex={mapZoom > 1 ? 0 : -1}>
                <div className="map-stage" style={{ width: `${mapZoom * 100}%`, height: `${mapZoom * 100}%` }}>
                <div className="map-plane">
                  <div className="floor-enter" key={floorLevel}>
              <MallMap
                payload={ready}
                floorLevel={floorLevel}
                selectedId={selectedId}
                startId={fromId === "" ? null : fromId}
                endId={toId === "" ? null : toId}
                route={route}
                showGraph={showGraph}
                traceLimit={traceLimit}
                perspective={perspective}
                stops={stops}
                onSelectLocation={(id) => {
                  if (id === null) {
                    setSelectedId(null);
                    return;
                  }
                  focusLocation(id);
                  if (window.matchMedia("(max-width: 899px)").matches) scrollToPanel();
                }}
              />
                  </div>
                </div>
                </div>
              </div>
              <div className="map-zoom-controls" role="group" aria-label="Map zoom controls">
                <button type="button" aria-label="Zoom out" disabled={mapZoom === 1} onClick={() => setMapZoom((zoom) => Math.max(1, zoom - 0.5))}><span aria-hidden="true">−</span></button>
                <output aria-label="Map zoom" aria-live="polite">{mapZoom}×</output>
                <button type="button" aria-label="Zoom in" disabled={mapZoom === 2} onClick={() => setMapZoom((zoom) => Math.min(2, zoom + 0.5))}><span aria-hidden="true">+</span></button>
              </div>
              <div className="map-canvas-caption"><span className="caption-dot" />{mapZoom > 1 ? "Scroll or swipe to explore" : perspective ? "A new perspective on your visit" : "Tap a place to see more"}</div>
            </div>
            <div className="map-legend" aria-label="Map legend">
              <span><i className="legend-square" /> Stores</span>
              <span><i className="legend-square food" /> Food & drink</span>
              <span><i className="legend-square services" /> Amenities</span>
              <span className="map-note">
                {route?.algorithm === "bfs" || route?.algorithm === "dfs"
                  ? "Numbers are the order the search checked"
                  : "Schematic floor plan"}
              </span>
            </div>
          </div>
          {routed.messages.map((message) => (
            <p key={message} data-testid="continue-via" className="continuation" role="status">
              <Icon name="elevator" size={16} />
              {message}
            </p>
          ))}
          <div className="visit-shortcuts" aria-label="Visit shortcuts">
            <button type="button" className="visit-shortcut shortcut-mint" onClick={() => { setPanelMode("plan"); scrollToPanel(); }}>
              <span className="shortcut-art" aria-hidden="true"><Icon name="list" size={22} /></span>
              <span><strong>More stops, less walking.</strong><small>Build your shopping route</small></span>
              <Icon name="send" size={15} />
            </button>
            <button type="button" className="visit-shortcut shortcut-peach" onClick={() => { setPanelMode("parking"); scrollToPanel(); }}>
              <span className="shortcut-art" aria-hidden="true"><Icon name="car" size={24} /></span>
              <span><strong>One less thing to remember.</strong><small>Save your parking spot</small></span>
              <Icon name="send" size={15} />
            </button>
          </div>
          <div className="map-footer">
            <span>{ready.mall.name} · Demo mall · Schematic routes</span>
            <button className="mobile-controls-link" type="button" onClick={scrollToPanel}>
              Plan your visit <Icon name="down" size={13} />
            </button>
            <label>
              <input type="checkbox" checked={showGraph} onChange={(event) => setShowGraph(event.target.checked)} className="accent-gold-400" />
              Show every hallway junction
            </label>
          </div>
        </section>
      </main>
      </div>
    </div>
  );
}

function BrandMark() {
  return (
    <span className="brand-mark">
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" aria-hidden>
        <path
          d="M4 19V6.5l8 7 8-7V19"
          stroke="currentColor"
          strokeWidth={2.4}
          strokeLinecap="round"
          strokeLinejoin="round"
        />
      </svg>
    </span>
  );
}
