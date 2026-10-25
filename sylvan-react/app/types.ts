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

export type SearchMode = 'cards' | 'printings';

export interface SearchResponse {
  mode: SearchMode;
  count: number;
  page: number;
  page_size: number;
  num_pages: number;
  pretty_query_message: string | null;
  error_message: string | null;
  results: SearchResult[];
}

export interface DeckSummary {
  id: number;
  name: string;
  subtitle: string | null;
  description: string | null;
  date_created: string;
  format: string;
  is_prototype: boolean;
  is_private: boolean;
}

export interface Paginated<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

export interface DeckCard {
  id: number;
  count: number;
  board: string;
  is_commander: boolean;
  card_id: number;
  card_name: string;
  layout: string;
  side: string | null;
  // A mana-font icon name such as "ability-companion"
  icon: string | null;
  image_url: string;
  // Only for cards with an image for each side, like transforming cards
  back_image_url: string | null;
  // Whether the front is printed sideways, like split cards and battles
  sideways: boolean;
}

export type BoardKey = 'main' | 'side' | 'maybe' | 'acquire';

export interface DeckDetail extends DeckSummary {
  last_modified: string;
  format_display: string;
  exclude_colours: number[];
  card_groups: { name: string; code: string; count: number; cards: DeckCard[] }[];
  sideboard: DeckCard[];
  mainboard_count: number;
  total_land_count: number;
  boards: Record<BoardKey, string>;
}

export interface ColourCount {
  count: number;
  name: string;
  symbol: string;
  chart_colour: string;
}

export interface ColourWeights {
  mana_symbols: ColourCount[];
  land_symbols: ColourCount[];
}
