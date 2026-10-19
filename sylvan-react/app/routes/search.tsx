import type { Route } from './+types/search';
import Search from '../components/Search';

export function meta({ location }: Route.MetaArgs) {
  const query = new URLSearchParams(location.search).get('query');
  return [{ title: query ? `${query} — Sylvan Library` : 'Search — Sylvan Library' }];
}

export default function SearchRoute() {
  return <Search />;
}
