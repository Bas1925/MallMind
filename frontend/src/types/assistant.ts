export interface SearchHit {
  location_id: string;
  name: string;
  slug: string;
  category: string;
  category_slug: string;
  floor: string;
  floor_level: number;
  score: number;
  match_type: string;
}

export interface AssistantAction {
  type: "highlight_location" | "show_route" | "change_floor";
  location_id?: string | null;
  from_location_id?: string | null;
  to_location_id?: string | null;
  floor_level?: number | null;
  profile?: string | null;
}

export interface AssistantResponse {
  answer: string;
  language: string;
  sources: Array<{
    location_id: string;
    name: string;
    slug: string;
    category_slug: string;
    floor: string;
    score: number;
  }>;
  actions: AssistantAction[];
  llm: string;
  tools: string[];
}
