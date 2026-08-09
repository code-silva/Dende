import { type RouteProp, useRoute } from "@react-navigation/native";
import { useCallback, useEffect } from "react";
import { FlatList, StyleSheet, Text, View } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { EmptyProductState } from "../components/EmptyProductState";
import { InfoBanner } from "../components/InfoBanner";
import { LoadingFooter } from "../components/LoadingFooter";
import { MarketBanner } from "../components/MarketBanner";
import ProductCard from "../components/ProductCard";
import { SearchBar } from "../components/SearchBar";
import { useProductsFetch } from "../hooks/useProductsFetch";
import type { HomeStackParamList } from "../types/navigation";

type SearchResultsRouteProp = RouteProp<
  HomeStackParamList,
  "SearchResultsScreen"
>;

export function SearchResultsScreen() {
  const route = useRoute<SearchResultsRouteProp>();
  const { query, selectedMarket, latitude, longitude } = route.params;

  const { products, isLoading, hasMoreData, fetchData } = useProductsFetch({
    latitude,
    longitude,
    query,
    marketId: selectedMarket?.id,
  });

  // --- SEARCH HEADER COMPONENT ---
  const SearchHeader = useCallback(
    () => (
      <View style={styles.headerContainer}>
        <SearchBar initialValue={query} />

        {selectedMarket && (
          <MarketBanner
            marketName={selectedMarket.name}
            subtitle={"OFERTAS DA REDE"}
          />
        )}

        <InfoBanner />

        <Text style={styles.resultsText}>
          {selectedMarket
            ? `Produtos em ${selectedMarket.name}`
            : `Resultados para "${query}"`}
        </Text>
      </View>
    ),
    [query, selectedMarket],
  );

  // biome-ignore lint/correctness/useExhaustiveDependencies: initial fetch on mount
  useEffect(() => {
    fetchData();
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
    return (
      <View style={styles.emptyStateContainer}>
        <Text style={styles.emptyStateTitle}>
          Nenhum produto encontrado para sua busca
        </Text>
        <Text style={styles.emptyStateSubtitle}>
          Tente buscar por outro termo ou verifique a ortografia do que digitou.
        </Text>
      </View>
    );
  };

  return (
    <SafeAreaView style={{ flex: 1, backgroundColor: "#F8F9FA" }}>
      <FlatList
        data={products}
        keyExtractor={(item) => item.id.toString()}
        renderItem={({ item, index }) => (
          <View style={styles.cardWrapper}>
            <ProductCard
              product={{ ...item, ranking: index + 1 }}
              handlePress={() => console.log("Clicked on product")}
              handleAddToList={() => console.log("Added to list")}
            />
          </View>
        )}
        numColumns={2}
        onEndReached={() => fetchData()}
        onEndReachedThreshold={0.5}
        ListFooterComponent={renderFooter}
        ListEmptyComponent={renderEmpty()}
        columnWrapperStyle={styles.gridRow}
        ListHeaderComponent={SearchHeader}
        contentContainerStyle={styles.gridContainer}
        showsVerticalScrollIndicator={false}
      />
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  headerContainer: {
    paddingBottom: 10,
  },
  gridContainer: {
    paddingHorizontal: 20,
    paddingBottom: 20,
  },
  gridRow: {
    justifyContent: "space-between",
  },
  cardWrapper: {
    flex: 1,
    marginHorizontal: 5,
    marginBottom: 10,
  },
  resultsText: {
    fontSize: 16,
    fontFamily: "Inter-Bold",
    color: "#333",
    marginVertical: 15,
    marginLeft: 10,
  },
  emptyStateContainer: {
    justifyContent: "center",
    alignItems: "center",
    padding: 24,
    marginTop: 24,
  },
  emptyStateTitle: {
    fontSize: 18,
    fontFamily: "Inter-Bold",
    color: "#333333",
    marginBottom: 6,
    textAlign: "center",
  },
  emptyStateSubtitle: {
    fontSize: 14,
    fontFamily: "Inter-Regular",
    color: "#888888",
    textAlign: "center",
    lineHeight: 20,
  },
});
