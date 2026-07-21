import type { Market } from "../types/market";
import type { Product } from "../types/product";
import type { MyListState } from "../types/list";
import { useAppStore } from "../store/useAppStore";

const initialState = {
  markets: [],
  homeHighlights: [],
  myList: null,
  isInitialDataLoaded: false,
};

const makeMarket = (id: number, name: string): Market => ({
  id,
  name,
  state: "SP",
  city: "São Paulo",
  address: `Rua ${name}, 100`,
  distanceInKilometers: id * 0.5,
  nameColor: null,
});

const makeProduct = (id: number, name: string): Product => ({
  id,
  productName: name,
  price: "R$ 10,00",
  marketName: "Mercado Teste",
  brand: "Marca Teste",
  image: "img.jpg",
  measurementUnit: "kg",
  measurement: "1",
  categoryName: "Teste",
});

describe("useAppStore", () => {
  beforeEach(() => {
    useAppStore.setState(initialState);
  });

  it("updates markets via setMarkets", () => {
    const mockMarkets = [makeMarket(1, "Super A"), makeMarket(2, "Super B")];

    useAppStore.getState().setMarkets(mockMarkets);

    const state = useAppStore.getState();
    expect(state.markets).toEqual(mockMarkets);
    expect(state.markets).toHaveLength(2);
  });

  it("updates homeHighlights via setHomeHighlights", () => {
    const mockHighlights = [
      makeProduct(1, "Arroz"),
      makeProduct(2, "Feijão"),
    ];

    useAppStore.getState().setHomeHighlights(mockHighlights);

    const state = useAppStore.getState();
    expect(state.homeHighlights).toEqual(mockHighlights);
    expect(state.homeHighlights).toHaveLength(2);
  });

  it("updates myList via setMyList", () => {
    const mockList: MyListState = {
      id: "list_abc",
      items: [
        {
          productId: 1,
          productName: "Arroz",
          quantity: 2,
          checked: false,
        },
      ],
      createdAt: new Date().toISOString(),
    };

    useAppStore.getState().setMyList(mockList);

    const state = useAppStore.getState();
    expect(state.myList).toEqual(mockList);
    expect(state.myList?.items).toHaveLength(1);
  });

  it("updates isInitialDataLoaded via setInitialDataLoaded", () => {
    expect(useAppStore.getState().isInitialDataLoaded).toBe(false);

    useAppStore.getState().setInitialDataLoaded(true);

    expect(useAppStore.getState().isInitialDataLoaded).toBe(true);
  });

  it("starts with the correct default values", () => {
    const state = useAppStore.getState();
    expect(state.markets).toEqual([]);
    expect(state.homeHighlights).toEqual([]);
    expect(state.myList).toBeNull();
    expect(state.isInitialDataLoaded).toBe(false);
  });
});
