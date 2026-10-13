import { HttpError } from "@/lib/api";

export function routeErrorMessage(error: unknown): string {
  if (error instanceof HttpError) {
    switch (error.code) {
      case "no_accessible_path":
        return "No wheelchair-accessible route between these locations. Try Walking, or pick a different pair.";
      case "no_path":
        return "No route exists between these locations.";
      case "unknown_location":
        return "That location is not on the map.";
      case "same_location":
        return "Pick two different places.";
      case "missing_anchor":
        return "This location is not connected to the routing graph.";
      case "unknown_mall":
        return "Mall map was not found.";
      default:
        return error.message || "Could not calculate a route.";
    }
  }
  if (error instanceof TypeError) {
    return "Backend unavailable. Start the API on port 8000 and try again.";
  }
  if (error instanceof Error && error.message !== "") {
    return error.message;
  }
  return "Something went wrong. Try again.";
}

export function mapErrorMessage(error: unknown): string {
  if (error instanceof HttpError) {
    if (error.code === "unknown_mall") return "This mall was not found.";
    return error.message || "Could not load the mall map.";
  }
  if (error instanceof TypeError) {
    return "Backend unavailable. The map cannot load until the API is running.";
  }
  if (error instanceof Error && error.message !== "") {
    return error.message;
  }
  return "Could not load the mall map.";
}
