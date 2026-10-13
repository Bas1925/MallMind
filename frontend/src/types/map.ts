export type RouteProfile = "normal" | "wheelchair" | "avoid_stairs";
export type CostMode = "distance" | "time";
export type SearchAlgorithm = "astar" | "bfs" | "dfs";

export interface MapMall {
  id: string;
  slug: string;
  name: string;
}

export interface MapFloor {
  id: string;
  level: number;
  name: string;
  display_order: number;
}

export interface MapLocation {
  id: string;
  slug: string;
  name: string;
  description: string | null;
  category_slug: string;
  category_name: string;
  floor_id: string;
  floor_level: number;
  floor_name: string;
  anchor_node_id: string | null;
  x: number | null;
  y: number | null;
  node_type: string | null;
  wheelchair_accessible: boolean;
}

export interface MapNode {
  id: string;
  floor_id: string;
  floor_level: number;
  x: number;
  y: number;
  node_type: string;
  location_id: string | null;
}

export interface MapEdge {
  id: string;
  from_node_id: string;
  to_node_id: string;
  from_floor_level: number;
  to_floor_level: number;
  edge_type: string;
  accessible: boolean;
}

export interface MallMapPayload {
  mall: MapMall;
  floors: MapFloor[];
  locations: MapLocation[];
  nodes: MapNode[];
  edges: MapEdge[];
}

export interface RouteResponse {
  route: string[];
  distance_m: number;
  estimated_seconds: number;
  floors: number[];
  instructions: string[];
  algorithm: string;
  nodes_expanded: number;
  profile: string;
  from_location: string;
  to_location: string;
  node_ids: string[];
  visited_ids?: string[];
}

export interface ApiError {
  code: string;
  message: string;
}

export function isApiError(value: unknown): value is ApiError {
  if (typeof value !== "object" || value === null) return false;
  if (!("code" in value) || !("message" in value)) return false;
  const { code, message } = value as { code: unknown; message: unknown };
  return typeof code === "string" && typeof message === "string";
}
