import type { MapEdge, MapNode, RouteResponse } from "@/types/map";

export interface Bounds {
  minX: number;
  minY: number;
  maxX: number;
  maxY: number;
}

const PAD = 20;

/** Backend y increases north; SVG y increases down. */
export function toSvg(x: number, y: number, bounds: Bounds): { x: number; y: number } {
  return { x, y: bounds.maxY - y };
}

export function boundsFor(nodes: MapNode[]): Bounds {
  if (nodes.length === 0) {
    return { minX: 0, minY: 0, maxX: 100, maxY: 80 };
  }
  let minX = Infinity;
  let minY = Infinity;
  let maxX = -Infinity;
  let maxY = -Infinity;
  for (const node of nodes) {
    minX = Math.min(minX, node.x);
    minY = Math.min(minY, node.y);
    maxX = Math.max(maxX, node.x);
    maxY = Math.max(maxY, node.y);
  }
  return {
    minX: minX - PAD,
    minY: minY - PAD,
    maxX: maxX + PAD,
    maxY: maxY + PAD,
  };
}

export function viewBox(bounds: Bounds): string {
  const width = bounds.maxX - bounds.minX;
  const height = bounds.maxY - bounds.minY;
  // toSvg maps original y=maxY → 0, so the SVG origin y is 0 after the flip.
  return `${bounds.minX} 0 ${width} ${height}`;
}

export function floorRect(bounds: Bounds): {
  x: number;
  y: number;
  width: number;
  height: number;
} {
  return {
    x: bounds.minX,
    y: 0,
    width: bounds.maxX - bounds.minX,
    height: bounds.maxY - bounds.minY,
  };
}

export function routeIds(route: RouteResponse): string[] {
  return route.node_ids.length > 0 ? route.node_ids : route.route;
}

export interface RouteSegment {
  floorLevel: number;
  points: Array<{ x: number; y: number }>;
}

export interface VerticalHop {
  fromLevel: number;
  toLevel: number;
  x: number;
  y: number;
  kind: "elevator" | "stairs" | "escalator";
}

export function routeOnFloor(
  nodes: MapNode[],
  edges: MapEdge[],
  route: RouteResponse,
  floorLevel: number,
): { segments: RouteSegment[]; hops: VerticalHop[] } {
  const byId = new Map(nodes.map((n) => [n.id, n]));
  const edgeByPair = new Map<string, MapEdge>();
  for (const edge of edges) {
    edgeByPair.set(`${edge.from_node_id}->${edge.to_node_id}`, edge);
  }

  const ids = routeIds(route);
  const segments: RouteSegment[] = [];
  const hops: VerticalHop[] = [];
  let current: Array<{ x: number; y: number }> = [];

  const flush = (): void => {
    if (current.length >= 2) {
      segments.push({ floorLevel, points: current });
    }
    current = [];
  };

  for (let i = 0; i < ids.length; i += 1) {
    const id = ids[i];
    if (id === undefined) continue;
    const node = byId.get(id);
    if (node === undefined) continue;
    const nextId = ids[i + 1];
    const next = nextId === undefined ? undefined : byId.get(nextId);

    if (node.floor_level === floorLevel) {
      current.push({ x: node.x, y: node.y });
    } else {
      flush();
    }

    if (next !== undefined && node.floor_level !== next.floor_level) {
      const edge = edgeByPair.get(`${node.id}->${next.id}`);
      const kind = hopKind(edge?.edge_type);
      if (node.floor_level === floorLevel || next.floor_level === floorLevel) {
        hops.push({
          fromLevel: node.floor_level,
          toLevel: next.floor_level,
          x: node.x,
          y: node.y,
          kind,
        });
      }
      flush();
    }
  }
  flush();
  return { segments, hops };
}

function hopKind(edgeType: string | undefined): VerticalHop["kind"] {
  if (edgeType === "elevator") return "elevator";
  if (edgeType === "stairs") return "stairs";
  if (edgeType === "escalator_up" || edgeType === "escalator_down" || edgeType === "escalator") {
    return "escalator";
  }
  return "elevator";
}

export function continueMessages(
  hops: VerticalHop[],
  floorLevel: number,
  floorName: (level: number) => string,
): string[] {
  const messages: string[] = [];
  for (const hop of hops) {
    if (hop.fromLevel === floorLevel && hop.toLevel !== floorLevel) {
      messages.push(`Continue via ${hop.kind} to ${floorName(hop.toLevel)}`);
    } else if (hop.toLevel === floorLevel && hop.fromLevel !== floorLevel) {
      messages.push(`Arrived via ${hop.kind} from ${floorName(hop.fromLevel)}`);
    }
  }
  return messages;
}

// Luminous tones that read on the dark map canvas.
export function categoryFill(slug: string): string {
  switch (slug) {
    case "fashion":
      return "#7aa2ff";
    case "electronics":
      return "#4fd1c5";
    case "food":
      return "#ffa45c";
    case "restroom":
      return "#5ec8ff";
    case "atm":
      return "#3ddc97";
    case "elevator":
      return "#b49cff";
    case "escalator":
      return "#d0a8ff";
    case "entrance":
      return "#f6f4ef";
    case "stairs":
      return "#a8a29e";
    case "services":
      return "#f9a8d4";
    case "entertainment":
      return "#ff6b81";
    default:
      return "#9aa0ab";
  }
}

export function formatDuration(seconds: number): string {
  const m = Math.max(1, Math.round(seconds / 60));
  return `${m} min`;
}
