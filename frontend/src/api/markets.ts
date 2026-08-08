import type { Market } from "../types/market";

const BASE_URL = process.env.EXPO_PUBLIC_API_URL;

const REQUEST_TIMEOUT_MS = 8000;

export async function fetchMarkets(
  latitude?: number,
  longitude?: number,
  address?: string,
  city?: string | null,
  radiusInKm: number = 50,
  signal?: AbortSignal,
): Promise<Market[]> {
  const url = new URL(`${BASE_URL}/nearby-markets/`);
  url.searchParams.append("latitude", String(latitude));
  url.searchParams.append("longitude", String(longitude));
  url.searchParams.append("radiusInKm", String(radiusInKm));
  if (address) url.searchParams.append("address", address);
  if (city) url.searchParams.append("city", city);

  const response = await fetch(url, { signal });
  const data = await response.json();
  return data.results as Market[];
}

export async function fetchSupermarkets(
  latitude?: number,
  longitude?: number,
  address?: string,
  city?: string | null,
  radiusInKm?: number,
  signal?: AbortSignal,
): Promise<Market[]> {
  return Promise.race([
    fetchMarkets(latitude, longitude, address, city, radiusInKm, signal),
    new Promise<never>((_, reject) =>
      setTimeout(
        () =>
          reject(new Error("Tempo limite excedido. Verifique sua conexão.")),
        REQUEST_TIMEOUT_MS,
      ),
    ),
  ]);
}
