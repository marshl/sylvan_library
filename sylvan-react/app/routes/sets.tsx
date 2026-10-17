import type { Route } from "./+types/sets";
import SetList from "../components/SetList";

export function meta({}: Route.MetaArgs) {
  return [{ title: "Sets — Sylvan Library" }];
}

export default function SetsRoute() {
  return <SetList />;
}
