export class ApiError extends Error {
  status: number;
  // The parsed JSON error response, e.g. DRF's {field: [messages]}
  body: unknown;

  constructor(status: number, message: string, body: unknown = null) {
    super(message);
    this.status = status;
    this.body = body;
  }
}

function getCookie(name: string): string | null {
  const match = document.cookie
    .split('; ')
    .find((row) => row.startsWith(`${name}=`));
  return match ? decodeURIComponent(match.split('=')[1]) : null;
}

const UNSAFE_METHODS = ['POST', 'PUT', 'PATCH', 'DELETE'];

/**
 * Fetches JSON from the Django API using the session cookie.
 * Unsafe methods get the CSRF token Django sets via /api/me/, and a plain
 * object body is sent as JSON.
 */
export async function fetchJson<T>(
  url: string,
  options: Omit<RequestInit, 'body'> & { body?: unknown } = {},
): Promise<T> {
  const { body, ...init } = options;
  const headers = new Headers(init.headers);
  headers.set('Accept', 'application/json');

  const method = (init.method ?? 'GET').toUpperCase();
  if (UNSAFE_METHODS.includes(method)) {
    const csrfToken = getCookie('csrftoken');
    if (csrfToken) headers.set('X-CSRFToken', csrfToken);
  }

  let requestBody: BodyInit | undefined;
  if (body instanceof FormData || typeof body === 'string') {
    requestBody = body;
  } else if (body !== undefined) {
    headers.set('Content-Type', 'application/json');
    requestBody = JSON.stringify(body);
  }

  const response = await fetch(url, {
    credentials: 'same-origin',
    ...init,
    headers,
    body: requestBody,
  });
  if (!response.ok) {
    let detail = `Request failed (${response.status})`;
    let data: unknown = null;
    try {
      data = await response.json();
      const body = data as { detail?: string };
      if (body?.detail) detail = body.detail;
    } catch {
      // not a JSON error body
    }
    throw new ApiError(response.status, detail, data);
  }
  if (response.status === 204) return undefined as T;
  return response.json();
}

export function isAbortError(err: unknown): boolean {
  return err instanceof DOMException && err.name === 'AbortError';
}
