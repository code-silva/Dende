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

interface SearchResultsScreenProps {
  route: {
    params: {
      query: string;
      selectedMarket: { id: number; name: string };
      latitude?: number;
      longitude?: number;
    };
  };
}

export function SearchResultsScreen({ route }: SearchResultsScreenProps) {
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
});
