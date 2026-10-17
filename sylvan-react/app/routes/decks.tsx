import type { Route } from "./+types/decks";
import Decks from "../components/Decks";

export function meta({}: Route.MetaArgs) {
  return [{ title: "Decks — Sylvan Library" }];
}

export default function DecksRoute() {
  return <Decks />;
}
