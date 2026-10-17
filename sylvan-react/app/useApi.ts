import { useEffect, useState } from 'react';
import { fetchJson, isAbortError } from './api';

interface ApiState<T> {
  data: T | null;
  loading: boolean;
  error: string | null;
}

/**
 * Fetches JSON from url whenever url or reloadKey changes. Pass null to skip
 * the request.
 */
export function useApi<T>(url: string | null, reloadKey: unknown = null): ApiState<T> {
  const [state, setState] = useState<ApiState<T>>({
    data: null,
    loading: url !== null,
    error: null,
  });

  useEffect(() => {
    if (url === null) {
      setState({ data: null, loading: false, error: null });
      return;
    }
    const controller = new AbortController();
    setState((s) => ({ ...s, loading: true, error: null }));
    fetchJson<T>(url, { signal: controller.signal })
      .then((data) => setState({ data, loading: false, error: null }))
      .catch((err) => {
        if (isAbortError(err)) return;
        setState({ data: null, loading: false, error: (err as Error).message });
      });
    return () => controller.abort();
  }, [url, reloadKey]);

  return state;
}
