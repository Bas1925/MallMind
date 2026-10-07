export interface PlannedStop {
  location_id: string;
  name: string;
  slug: string;
  floor: string;
  floor_level: number;
  position: number;
}

export interface OptimizeResponse {
  original_order: PlannedStop[];
  optimized_order: PlannedStop[];
  original_distance_m: number;
  optimized_distance_m: number;
  distance_saved_m: number;
  distance_saved_percent: number | null;
  original_seconds: number;
  optimized_seconds: number;
  estimated_time_saved_seconds: number;
  floor_changes_original: number;
  floor_changes_optimized: number;
  algorithm: string;
  improved: boolean;
  message: string | null;
  node_ids: string[];
  instructions: string[];
  floors: number[];
  profile: string;
  cost_mode: string;
  astar_calls: number;
  two_opt_moves: number;
  nearest_neighbor_distance_m: number;
  nearest_neighbor_2opt_distance_m: number;
  exact_distance_m: number | null;
  nearest_neighbor_gap_percent: number | null;
  nearest_neighbor_2opt_gap_percent: number | null;
  matrix_m: Array<Array<number | null>>;
  labels: string[];
}
