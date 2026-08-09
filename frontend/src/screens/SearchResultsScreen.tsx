import { type RouteProp, useRoute } from "@react-navigation/native";
import { useCallback, useEffect } from "react";
import { StyleSheet, Text, View } from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { AiInfoBanner } from "../components/AiInfoBanner";
import { EmptyProductState } from "../components/EmptyProductState";
import { EmptySearchState } from "../components/EmptySearchState";
import { LoadingFooter } from "../components/LoadingFooter";
import { MarketBanner } from "../components/MarketBanner";
import { ProductGrid } from "../components/ProductGrid";
import { SearchBar } from "../components/SearchBar";
import { useProductsFetch } from "../hooks/useProductsFetch";
import type { HomeStackParamList } from "../types/navigation";
import type { Product } from "../types/product";

type SearchResultsRouteProp = RouteProp<
  HomeStackParamList,
  "SearchResultsScreen"
>;

export function SearchResultsScreen() {
  const route = useRoute<SearchResultsRouteProp>();
  const { query, selectedMarket, latitude, longitude } = route.params;
  const insets = useSafeAreaInsets();

  const { products, isLoading, hasMoreData, fetchData } = useProductsFetch({
    latitude,
    longitude,
    query,
    marketId: selectedMarket?.id,
  });

  // --- SEARCH HEADER COMPONENT ---
  const SearchHeader = useCallback(
    () => (
      <View style={[styles.headerContainer, { paddingTop: insets.top }]}>
        <SearchBar initialValue={query} />

        {selectedMarket && (
          <MarketBanner
            marketName={selectedMarket.name}
            subtitle={"OFERTAS DA REDE"}
          />
        )}

        <AiInfoBanner />

        <Text style={styles.resultsText}>
          {selectedMarket
            ? `Produtos em ${selectedMarket.name}`
            : `Resultados para "${query}"`}
        </Text>
      </View>
    ),
    [insets, query, selectedMarket],
  );

  // biome-ignore lint/correctness/useExhaustiveDependencies: initial fetch on mount
  useEffect(() => {
    fetchData();
  }, []);

  const handleProductPress = useCallback((_product: Product) => {
    console.log("Clicked on product");
  }, []);

  const handleAddToList = useCallback((_product: Product) => {
    console.log("Added to list");
  }, []);

  const renderFooter = () => {
    if (isLoading) {
      return <LoadingFooter isLoading={isLoading} />;
    }
    if (!hasMoreData && products.length > 0) {
      return <EmptyProductState />;
    }
    return null;
  };

  const renderEmpty = () => {
    if (isLoading) return null;
    return <EmptySearchState query={query} />;
  };

  return (
    <View style={styles.container}>
      <ProductGrid
        products={products}
        handlePress={handleProductPress}
        handleAddToList={handleAddToList}
        onEndReached={() => fetchData()}
        onEndReachedThreshold={0.5}
        listFooterComponent={renderFooter()}
        listHeaderComponent={<SearchHeader />}
        listEmptyComponent={renderEmpty()}
        contentContainerStyle={[
          styles.gridContainer,
          { paddingBottom: insets.bottom + 5 },
        ]}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: "#F8F9FA",
  },
  headerContainer: {
    paddingBottom: 10,
  },
  gridContainer: {
    paddingHorizontal: 16,
    paddingTop: 8,
  },
  resultsText: {
    fontSize: 16,
    fontFamily: "Inter-Bold",
    color: "#333",
    marginVertical: 15,
    marginLeft: 10,
  },
});
