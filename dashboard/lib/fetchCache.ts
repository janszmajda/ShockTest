/**
 * Ultra-simple module-level fetch cache.
 *
 * Module scope persists across Next.js client-side navigations (the SPA shell
 * keeps the same JS context), so navigating / → /portfolio → /shock/[id] will
 * re-use cached responses instead of hitting the API again.
 *
 * Zero dependencies. Entries expire after `ttl` ms (default 30 s).
 */

interface CacheEntry {
  data: unknown;
  ts: number;
  /** In-flight promise so concurrent callers deduplicate. */
  pending?: Promise<unknown>;
}

const store = new Map<string, CacheEntry>();
const DEFAULT_TTL = 30_000; // 30 seconds

export async function cachedFetch<T>(
  url: string,
  ttl = DEFAULT_TTL,
): Promise<T> {
  const now = Date.now();
  const hit = store.get(url);

  // Return cached data if still fresh
  if (hit && now - hit.ts < ttl) return hit.data as T;

  // Deduplicate concurrent in-flight requests for the same URL
  if (hit?.pending) return hit.pending as Promise<T>;

  const pending = fetch(url)
    .then((res) => {
      if (!res.ok) throw new Error(`Fetch failed: ${res.status} ${url}`);
      return res.json();
    })
    .then((data: T) => {
      store.set(url, { data, ts: Date.now() });
      return data;
    })
    .catch((err) => {
      // Clear pending on error so next caller retries
      store.delete(url);
      throw err;
    });

  store.set(url, { ...(hit ?? { data: null, ts: 0 }), pending });
  return pending as Promise<T>;
}

/** Force-invalidate a specific URL (useful after mutations). */
export function invalidate(url: string) {
  store.delete(url);
}
