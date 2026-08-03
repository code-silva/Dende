const BASE_URL = process.env.EXPO_PUBLIC_API_URL;

export async function fetchProducts(
  latitude: number | undefined,
  longitude: number | undefined,
  page: number = 1,
  query?: string,
  marketId?: number,
  signal?: AbortSignal,
) {
  const url = new URL(`${BASE_URL}/products/offers/`);
  url.searchParams.append("page", String(page));
  url.searchParams.append("latitude", String(latitude));
  url.searchParams.append("longitude", String(longitude));

  if (query) url.searchParams.append("query", query);
  if (marketId) url.searchParams.append("marketId", String(marketId));

  const response = await fetch(url, { signal });
  return await response.json();
}
