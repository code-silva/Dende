import type { Market } from "../types/market";

const BASE_URL = process.env.EXPO_PUBLIC_API_URL;

export async function fetchMarkets(
  latitude?: number,
  longitude?: number,
  signal?: AbortSignal,
): Promise<Market[]> {
  const url = new URL(`${BASE_URL}/nearby-markets/`);
  url.searchParams.append("latitude", String(latitude));
  url.searchParams.append("longitude", String(longitude));

  const response = await fetch(url, { signal });
  const data = await response.json();
  return data.results as Market[];
}
