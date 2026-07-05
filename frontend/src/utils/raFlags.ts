import type { ImageSourcePropType } from "react-native";

interface RAConfig {
  flag: ImageSourcePropType;
  neighborhoodKeywords: string[];
}

const raFlagsMap: Record<string, RAConfig> = {
  gama: {
    flag: require("../assets/flags/ra_gama.jpg"),
    neighborhoodKeywords: [
      "gama sul",
      "setor oeste",
      "setor central",
      "gama norte",
    ],
  },
  "santa maria": {
    flag: require("../assets/flags/ra_santa_maria.jpg"),
    neighborhoodKeywords: [
      "santa maria sul",
      "santa maria norte",
      "setor residencial",
      "cl",
    ],
  },
  guara: {
    flag: require("../assets/flags/ra_guara.png"),
    neighborhoodKeywords: ["guará i", "guará ii", "guará iii"],
  },
  // Future compound RAs follow the same pattern with ASCII keys:
  // aguas_claras: { ... }
};

/**
 * Helper function to remove accents and special characters,
 * ensuring searches for "águas claras" and "aguas claras" match identically.
 */
function normalizeString(text: string): string {
  return text
    .toLowerCase()
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .trim();
}

export function findFlag(
  neighborhood?: string,
  city?: string,
): ImageSourcePropType | undefined {
  const neighborhoodText = normalizeString(neighborhood ?? "");
  const cityText = normalizeString(city ?? "");

  // Phase 1: Match by neighborhood keywords (highest priority)
  for (const ra of Object.values(raFlagsMap)) {
    const matchesNeighborhood = ra.neighborhoodKeywords.some((keyword) =>
      neighborhoodText.includes(normalizeString(keyword)),
    );
    if (matchesNeighborhood) return ra.flag;
  }

  // Phase 2: Fallback to city/RA (works perfectly with compound names like "santa maria")
  for (const [raKey, ra] of Object.entries(raFlagsMap)) {
    if (cityText.includes(normalizeString(raKey))) {
      return ra.flag;
    }
  }

  return undefined;
}

export function getDisplayText(neighborhood?: string, city?: string): string {
  const neighborhoodClean = neighborhood?.trim();
  if (neighborhoodClean) return neighborhoodClean;
  return city?.trim() ?? "";
}
