import type { Market } from "../types/market";
import { normalizeString, searchMarkets } from "../utils/fuzzySearch";

const makeMarket = (id: number, name: string, address?: string): Market => ({
  id,
  name,
  state: "DF",
  city: "Brasília",
  address: address ?? `Endereço ${name}`,
  distanceInKilometers: id * 0.5,
  nameColor: null,
});

const markets: Market[] = [
  makeMarket(1, "Comper"),
  makeMarket(2, "Ponto Alto"),
  makeMarket(3, "Vivendas"),
  makeMarket(4, "São José"),
  makeMarket(5, "Extra"),
];

describe("normalizeString", () => {
  it("lowercases and removes diacritics", () => {
    expect(normalizeString("São José")).toBe("sao jose");
    expect(normalizeString("  Guará  ")).toBe("guara");
  });
});

describe("searchMarkets", () => {
  it("returns the full list when query is empty", () => {
    expect(searchMarkets(markets, "  ")).toEqual(markets);
  });

  it("finds Comper when user types 'conper'", () => {
    const result = searchMarkets(markets, "conper");
    expect(result.map((m) => m.name)).toContain("Comper");
  });

  it("finds Ponto Alto regardless of case", () => {
    const result = searchMarkets(markets, "ponto alto");
    expect(result.map((m) => m.name)).toContain("Ponto Alto");
  });

  it("finds Vivendas when user types 'vivenda'", () => {
    const result = searchMarkets(markets, "vivenda");
    expect(result.map((m) => m.name)).toContain("Vivendas");
  });

  it("finds São José when user types 'sao'", () => {
    const result = searchMarkets(markets, "sao");
    expect(result.map((m) => m.name)).toContain("São José");
  });

  it("does not return completely irrelevant results", () => {
    const result = searchMarkets(markets, "xyzabc");
    expect(result).toHaveLength(0);
  });

  it("sorts results by relevance", () => {
    const result = searchMarkets(markets, "comper");
    expect(result[0].name).toBe("Comper");
  });
});
