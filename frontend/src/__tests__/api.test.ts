import type { Market } from "../types/market";
import {
  fetchNearbyMarkets,
  fetchHomeHighlights,
  fetchMyListInitialState,
} from "../api/api";
import { fetchMarkets } from "../api/markets";
import { fetchProducts } from "../api/products";

jest.mock("../api/markets");
jest.mock("../api/products");

const mockedFetchMarkets = jest.mocked(fetchMarkets);
const mockedFetchProducts = jest.mocked(fetchProducts);

const makeMarket = (id: number, name: string): Market => ({
  id,
  name,
  state: "SP",
  city: "São Paulo",
  address: `Rua ${name}, 100`,
  distanceInKilometers: id * 0.5,
  nameColor: null,
});

describe("fetchNearbyMarkets", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("calls fetchMarkets with coordinates and returns markets", async () => {
    const mockMarkets = [makeMarket(1, "Supermarket A"), makeMarket(2, "Supermarket B")];
    mockedFetchMarkets.mockResolvedValue(mockMarkets);

    const result = await fetchNearbyMarkets(-23.5, -46.6);

    expect(mockedFetchMarkets).toHaveBeenCalledTimes(1);
    expect(mockedFetchMarkets).toHaveBeenCalledWith(-23.5, -46.6);
    expect(result).toEqual(mockMarkets);
  });

  it("calls fetchMarkets without coordinates when not provided", async () => {
    mockedFetchMarkets.mockResolvedValue([]);

    await fetchNearbyMarkets();

    expect(mockedFetchMarkets).toHaveBeenCalledWith(undefined, undefined);
  });

  it("rejects when fetchMarkets fails", async () => {
    const error = new Error("Network error");
    mockedFetchMarkets.mockRejectedValue(error);

    await expect(fetchNearbyMarkets(-23.5, -46.6)).rejects.toThrow(
      "Network error",
    );
  });
});

describe("fetchHomeHighlights", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("calls fetchProducts with page=1 and returns offers", async () => {
    const mockOffers = {
      results: [
        { id: 1, productName: "Arroz", price: "R$ 5,00", marketName: "Mercado A", brand: "Brand A", image: "img1.jpg", measurementUnit: "kg", measurement: "1", categoryName: "Grãos" },
        { id: 2, productName: "Feijão", price: "R$ 7,50", marketName: "Mercado B", brand: "Brand B", image: "img2.jpg", measurementUnit: "kg", measurement: "1", categoryName: "Grãos" },
      ],
    };
    mockedFetchProducts.mockResolvedValue(mockOffers);

    const result = await fetchHomeHighlights(-23.5, -46.6);

    expect(mockedFetchProducts).toHaveBeenCalledTimes(1);
    expect(mockedFetchProducts).toHaveBeenCalledWith(-23.5, -46.6, 1);
    expect(result).toEqual(mockOffers);
  });

  it("calls fetchProducts without coordinates when not provided", async () => {
    mockedFetchProducts.mockResolvedValue({ results: [] });

    await fetchHomeHighlights();

    expect(mockedFetchProducts).toHaveBeenCalledWith(undefined, undefined, 1);
  });

  it("rejects when fetchProducts fails", async () => {
    const error = new Error("Server error");
    mockedFetchProducts.mockRejectedValue(error);

    await expect(fetchHomeHighlights(-23.5, -46.6)).rejects.toThrow(
      "Server error",
    );
  });
});

describe("fetchMyListInitialState", () => {
  beforeEach(() => {
    jest.useFakeTimers();
  });

  afterEach(() => {
    jest.useRealTimers();
  });

  it("returns the expected initial shopping list structure after 1 second", async () => {
    const promise = fetchMyListInitialState();

    jest.advanceTimersByTime(1000);

    const result = await promise;

    expect(result).toHaveProperty("id");
    expect(typeof result.id).toBe("string");
    expect(result).toHaveProperty("items");
    expect(result.items).toEqual([]);
    expect(result).toHaveProperty("createdAt");
    expect(typeof result.createdAt).toBe("string");
    expect(() => new Date(result.createdAt)).not.toThrow();
  });
});
