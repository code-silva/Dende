import Fuse, { type IFuseOptions } from "fuse.js";
import type { Market } from "../types/market";

const FUZZY_SEARCH_THRESHOLD = 0.35;

const fuseOptions: IFuseOptions<Market> = {
  keys: [
    { name: "name", weight: 2 },
    { name: "address", weight: 1 },
  ],
  threshold: FUZZY_SEARCH_THRESHOLD,
  ignoreLocation: true,
  ignoreDiacritics: true,
  shouldSort: true,
};

export function normalizeString(text: string): string {
  return text
    .toLowerCase()
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .trim();
}

export function searchMarkets(markets: Market[], query: string): Market[] {
  const cleanQuery = query.trim();
  if (!cleanQuery) return markets;

  const fuse = new Fuse(markets, fuseOptions);
  return fuse.search(cleanQuery).map((result) => result.item);
}
