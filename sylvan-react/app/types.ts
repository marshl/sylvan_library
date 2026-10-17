// Shapes returned by the Django API. Only the fields the app uses are listed.

export interface CardFace {
  id: number;
  name: string;
  side: string | null;
  mana_cost: string | null;
  mana_value: number;
  type_line: string | null;
  rules_text: string | null;
  power: string | null;
  toughness: string | null;
  loyalty: string | null;
  types: string[];
  subtypes: string[];
}

export interface CardFacePrinting {
  id: number;
  image_url: string;
}

export interface CardSet {
  id: number;
  name: string;
  code: string;
}

export interface Rarity {
  id: number;
  name: string;
  symbol: string;
}

export interface CardPrinting {
  id: number;
  number: string | null;
  set: CardSet;
  rarity: Rarity;
  keyrune_code: string;
  // null for anonymous users
  owned_count: number | null;
  face_printings: CardFacePrinting[];
}

export interface Card {
  id: number;
  name: string;
  layout: string;
  faces: CardFace[];
  printings: CardPrinting[];
  // null for anonymous users
  owned_count: number | null;
}

export interface SearchResult {
  card: Card;
  selected_printing: CardPrinting;
}

export interface SearchResponse {
  count: number;
  page: number;
  page_size: number;
  num_pages: number;
  pretty_query_message: string | null;
  error_message: string | null;
  results: SearchResult[];
}
