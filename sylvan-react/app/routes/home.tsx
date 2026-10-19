import type { Route } from './+types/home';

export function meta({}: Route.MetaArgs) {
  return [{ title: 'Sylvan Library' }];
}

export default function Home() {
  return (
    <div>
      <h1>Welcome to Sylvan Library</h1>
      <p>
        This is a placeholder home page. You can navigate to the other pages using the links in the
        top bar.
      </p>
    </div>
  );
}
