import type { Route } from "./+types/search";
import Search from "../components/Search";

export function meta({}: Route.MetaArgs) {
  return [{ title: "Search — Sylvan Library" }];
}

export default function SearchRoute() {
  return <Search />;
}
