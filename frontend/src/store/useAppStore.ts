import { create } from "zustand";
import type { MyListState } from "../types/list";
import type { Market } from "../types/market";
import type { Product } from "../types/product";

export interface AppStore {
  markets: Market[];
  homeHighlights: Product[];
  myList: MyListState | null;
  isInitialDataLoaded: boolean;
  preFetchError: string | null;
  isRetrying: boolean;
  setMarkets: (markets: Market[]) => void;
  setHomeHighlights: (products: Product[]) => void;
  setMyList: (myList: MyListState) => void;
  setInitialDataLoaded: (loaded: boolean) => void;
  setPreFetchError: (error: string | null) => void;
  setIsRetrying: (retrying: boolean) => void;
}

export const useAppStore = create<AppStore>((set) => ({
  markets: [],
  homeHighlights: [],
  myList: null,
  isInitialDataLoaded: false,
  preFetchError: null,
  isRetrying: false,
  setMarkets: (markets) => set({ markets }),
  setHomeHighlights: (homeHighlights) => set({ homeHighlights }),
  setMyList: (myList) => set({ myList }),
  setInitialDataLoaded: (isInitialDataLoaded) => set({ isInitialDataLoaded }),
  setPreFetchError: (preFetchError) => set({ preFetchError }),
  setIsRetrying: (isRetrying) => set({ isRetrying }),
}));
