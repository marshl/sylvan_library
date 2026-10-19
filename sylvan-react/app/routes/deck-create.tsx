import type { Route } from './+types/deck-create';
import DeckEdit from '../components/DeckEdit';
import RequireLogin from '../components/RequireLogin';

export function meta({}: Route.MetaArgs) {
  return [{ title: 'New deck — Sylvan Library' }];
}

export default function DeckCreateRoute() {
  return (
    <RequireLogin what="create a deck">
      <DeckEdit deckId={null} />
    </RequireLogin>
  );
}
