import { fetchMarkets } from "./markets";
import { fetchProducts } from "./products";
import type { MyListState } from "../types/list";

export function fetchNearbyMarkets(latitude?: number, longitude?: number) {
  return fetchMarkets(latitude, longitude);
}

export function fetchHomeHighlights(latitude?: number, longitude?: number) {
  return fetchProducts(latitude, longitude, 1);
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
