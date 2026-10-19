import type { Route } from './+types/deck-stats';
import DeckStats from '../components/DeckStats';

export function meta({}: Route.MetaArgs) {
  return [{ title: 'Deck stats — Sylvan Library' }];
}

export default function DeckStatsRoute() {
  return <DeckStats />;
}
