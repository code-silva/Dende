import type { MyListState } from "../types/list";
import { fetchMarkets } from "./markets";
import { fetchProducts } from "./products";

const PRE_FETCH_TIMEOUT_MS = 8000;

function fetchWithTimeout<T>(promise: Promise<T>, ms: number): Promise<T> {
  return Promise.race([
    promise,
    new Promise<never>((_, reject) =>
      setTimeout(
        () =>
          reject(new Error("Tempo limite excedido. Verifique sua conexão.")),
        ms,
      ),
    ),
  ]);
}

export function fetchNearbyMarkets(
  latitude?: number,
  longitude?: number,
  signal?: AbortSignal,
) {
  return fetchWithTimeout(
    fetchMarkets(latitude, longitude, signal),
    PRE_FETCH_TIMEOUT_MS,
  );
}

export function fetchHomeHighlights(
  latitude?: number,
  longitude?: number,
  signal?: AbortSignal,
) {
  return fetchWithTimeout(
    fetchProducts(latitude, longitude, 1, undefined, undefined, signal),
    PRE_FETCH_TIMEOUT_MS,
  );
}

export function fetchMyListInitialState(): Promise<MyListState> {
  return new Promise((resolve) => {
    setTimeout(() => {
      resolve({
        id: `list_${Date.now()}_${Math.random().toString(36).slice(2, 9)}`,
        items: [],
        createdAt: new Date().toISOString(),
      });
    }, 1000);
  });
}

export { PRE_FETCH_TIMEOUT_MS };
