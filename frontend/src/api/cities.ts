const BASE_URL = process.env.EXPO_PUBLIC_API_URL;

export async function fetchCities(signal?: AbortSignal): Promise<string[]> {
  const url = new URL(`${BASE_URL}/cities/`);

  const response = await fetch(url, { signal });
  const data = await response.json();
  return data as string[];
}
