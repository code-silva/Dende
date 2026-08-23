export interface SelectedMarket {
  id: number;
  name: string;
}

export type HomeStackParamList = {
  // biome-ignore lint/style/useNamingConvention: route names use PascalCase
  HomeScreen: undefined;
  // biome-ignore lint/style/useNamingConvention: route names use PascalCase
  SearchResultsScreen: {
    query: string;
    selectedMarket?: SelectedMarket;
    latitude?: number;
    longitude?: number;
  };
  // biome-ignore lint/style/useNamingConvention: route names use PascalCase
  StoreProductsScreen: {
    selectedMarket: SelectedMarket;
    latitude?: number;
    longitude?: number;
  };
};
