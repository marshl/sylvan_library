import { type RouteConfig, index, route } from '@react-router/dev/routes';

export default [
  index('routes/home.tsx'),
  route('search', 'routes/search.tsx'),
  route('sets', 'routes/sets.tsx'),
  route('decks', 'routes/decks.tsx'),
  route('decks/create', 'routes/deck-create.tsx'),
  route('decks/stats', 'routes/deck-stats.tsx'),
  route('decks/:deckId', 'routes/deck.tsx'),
  route('decks/:deckId/edit', 'routes/deck-edit.tsx'),
] satisfies RouteConfig;
