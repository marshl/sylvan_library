import type { Route } from "./+types/deck-edit";
import DeckEdit from "../components/DeckEdit";
import RequireLogin from "../components/RequireLogin";

export function meta({}: Route.MetaArgs) {
  return [{ title: "Edit deck — Sylvan Library" }];
}

export default function DeckEditRoute({ params }: Route.ComponentProps) {
  return (
    <RequireLogin what="edit this deck">
      <DeckEdit key={params.deckId} deckId={Number(params.deckId)} />
    </RequireLogin>
  );
}
