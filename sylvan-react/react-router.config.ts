import type { Config } from "@react-router/dev/config";

export default {
  // SPA mode: Django hosts the shell; RR does client-only routing.
  ssr: false,
  // Django mounts the SPA under /react/.
  basename: "/react/",
} satisfies Config;
