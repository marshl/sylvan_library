import type { Route } from './+types/deck';
import DeckView from '../components/DeckView';
import RequireLogin from '../components/RequireLogin';

export function meta({}: Route.MetaArgs) {
  return [{ title: 'Deck — Sylvan Library' }];
}

export default function DeckRoute({ params }: Route.ComponentProps) {
  return (
    <RequireLogin what="see this deck">
      <DeckView key={params.deckId} deckId={Number(params.deckId)} />
    </RequireLogin>
  );
}
