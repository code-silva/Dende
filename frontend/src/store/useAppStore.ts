import { create } from "zustand";
import type { Market } from "../types/market";
import type { Product } from "../types/product";
import type { MyListState } from "../types/list";

export interface AppStore {
  markets: Market[];
  homeHighlights: Product[];
  myList: MyListState | null;
  isInitialDataLoaded: boolean;
  setMarkets: (markets: Market[]) => void;
  setHomeHighlights: (products: Product[]) => void;
  setMyList: (myList: MyListState) => void;
  setInitialDataLoaded: (loaded: boolean) => void;
}

export const useAppStore = create<AppStore>((set) => ({
  markets: [],
  homeHighlights: [],
  myList: null,
  isInitialDataLoaded: false,
  setMarkets: (markets) => set({ markets }),
  setHomeHighlights: (homeHighlights) => set({ homeHighlights }),
  setMyList: (myList) => set({ myList }),
  setInitialDataLoaded: (isInitialDataLoaded) => set({ isInitialDataLoaded }),
}));
