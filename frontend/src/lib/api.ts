import type { AssistantResponse, SearchHit } from "@/types/assistant";
import type { OptimizeResponse } from "@/types/tour";
import { isApiError, type MallMapPayload, type RouteProfile, type RouteResponse } from "@/types/map";

const API_URL = process.env["NEXT_PUBLIC_API_URL"] ?? "http://localhost:8000";

export class HttpError extends Error {
  readonly status: number;
  readonly code: string;

  constructor(status: number, code: string, message: string) {
    super(message);
    this.status = status;
    this.code = code;
  }
}

async function parseJson(res: Response): Promise<unknown> {
  return (await res.json()) as unknown;
}

export async function fetchMallMap(slug: string, signal?: AbortSignal): Promise<MallMapPayload> {
  const init: RequestInit = { cache: "no-store" };
  if (signal !== undefined) {
    init.signal = signal;
  }
  const res = await fetch(`${API_URL}/api/v1/malls/${encodeURIComponent(slug)}/map`, init);
  const body: unknown = await parseJson(res);
  if (!res.ok) {
    if (isApiError(body)) throw new HttpError(res.status, body.code, body.message);
    throw new HttpError(res.status, "map_failed", "Could not load the mall map");
  }
  return body as MallMapPayload;
}

export async function requestRoute(input: {
  fromLocationId: string;
  toLocationId: string;
  profile: RouteProfile;
}): Promise<RouteResponse> {
  const res = await fetch(`${API_URL}/api/v1/navigation/route`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    cache: "no-store",
    body: JSON.stringify({
      from_location_id: input.fromLocationId,
      to_location_id: input.toLocationId,
      profile: input.profile,
      cost_mode: "distance",
    }),
  });
  const body: unknown = await parseJson(res);
  if (!res.ok) {
    if (isApiError(body)) throw new HttpError(res.status, body.code, body.message);
    throw new HttpError(res.status, "route_failed", "Could not calculate a route");
  }
  return body as RouteResponse;
}

export async function searchLocations(query: string): Promise<SearchHit[]> {
  const params = new URLSearchParams({ q: query, mall: "nova-mall" });
  const res = await fetch(`${API_URL}/api/v1/search?${params.toString()}`, { cache: "no-store" });
  const body: unknown = await parseJson(res);
  if (!res.ok) {
    if (isApiError(body)) throw new HttpError(res.status, body.code, body.message);
    throw new HttpError(res.status, "search_failed", "Search failed");
  }
  if (!isSearchBody(body)) throw new HttpError(res.status, "search_failed", "Unexpected search response");
  return body.results;
}

export async function askAssistant(input: {
  message: string;
  currentLocationId: string | null;
  profile: RouteProfile;
}): Promise<AssistantResponse> {
  const payload: Record<string, string> = {
    message: input.message,
    routing_profile: input.profile,
  };
  if (input.currentLocationId !== null) {
    payload["current_location_id"] = input.currentLocationId;
  }
  const res = await fetch(`${API_URL}/api/v1/assistant/query`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    cache: "no-store",
    body: JSON.stringify(payload),
  });
  const body: unknown = await parseJson(res);
  if (!res.ok) {
    if (isApiError(body)) throw new HttpError(res.status, body.code, body.message);
    throw new HttpError(res.status, "assistant_failed", "Assistant failed");
  }
  if (!isAssistantBody(body)) {
    throw new HttpError(res.status, "assistant_failed", "Unexpected assistant response");
  }
  return body;
}

export async function optimizeTour(input: {
  startLocationId: string;
  locationIds: string[];
  profile: RouteProfile;
}): Promise<OptimizeResponse> {
  const res = await fetch(`${API_URL}/api/v1/navigation/optimize`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    cache: "no-store",
    body: JSON.stringify({
      start_location_id: input.startLocationId,
      location_ids: input.locationIds,
      profile: input.profile,
      cost_mode: "distance",
    }),
  });
  const body: unknown = await parseJson(res);
  if (!res.ok) {
    if (isApiError(body)) throw new HttpError(res.status, body.code, body.message);
    throw new HttpError(res.status, "optimize_failed", "Could not optimize the route");
  }
  if (!isOptimizeBody(body)) {
    throw new HttpError(res.status, "optimize_failed", "Unexpected optimize response");
  }
  return body;
}

function isOptimizeBody(value: unknown): value is OptimizeResponse {
  if (typeof value !== "object" || value === null) return false;
  if (!("optimized_order" in value) || !("optimized_distance_m" in value)) return false;
  const record = value as { optimized_order: unknown; optimized_distance_m: unknown };
  return Array.isArray(record.optimized_order) && typeof record.optimized_distance_m === "number";
}

function isSearchBody(value: unknown): value is { results: SearchHit[] } {
  if (typeof value !== "object" || value === null || !("results" in value)) return false;
  const results = (value as { results: unknown }).results;
  return Array.isArray(results);
}

function isAssistantBody(value: unknown): value is AssistantResponse {
  if (typeof value !== "object" || value === null) return false;
  if (!("answer" in value) || !("language" in value) || !("actions" in value)) return false;
  const record = value as { answer: unknown; language: unknown; actions: unknown };
  return typeof record.answer === "string" && typeof record.language === "string" && Array.isArray(record.actions);
}

export { API_URL };
