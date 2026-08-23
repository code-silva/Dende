import {
  type RouteProp,
  useNavigation,
  useRoute,
} from "@react-navigation/native";
import type { NativeStackNavigationProp } from "@react-navigation/native-stack";
import { useCallback, useEffect, useRef, useState } from "react";
import { type FlatList, Keyboard, StyleSheet, Text, View } from "react-native";
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

type SearchResultsNavigationProp = NativeStackNavigationProp<
  HomeStackParamList,
  "SearchResultsScreen"
>;

export function SearchResultsScreen() {
  const route = useRoute<SearchResultsRouteProp>();
  const navigation = useNavigation<SearchResultsNavigationProp>();
  const { selectedMarket, latitude, longitude } = route.params;
  const insets = useSafeAreaInsets();

  const [searchTerm, setSearchTerm] = useState(route.params.query);
  const listRef = useRef<FlatList<Product>>(null);

  const { products, isLoading, hasMoreData, fetchData } = useProductsFetch({
    latitude,
    longitude,
    query: searchTerm,
    marketId: selectedMarket?.id,
  });

  // Keeps the single source of truth in sync when route params change
  // (e.g. a new query submitted from this screen or re-navigation).
  useEffect(() => {
    setSearchTerm(route.params.query);
  }, [route.params.query]);

  const initialFetchRef = useRef(false);

  useEffect(() => {
    if (!initialFetchRef.current) {
      initialFetchRef.current = true;
      fetchData();
    }
  }, [fetchData]);

  const handleSearchSubmit = useCallback(
    (text: string) => {
      Keyboard.dismiss();
      const trimmed = text.trim();
      if (!trimmed) return;

      setSearchTerm(trimmed);
      navigation.setParams({ query: trimmed });
      fetchData(trimmed, true);
      listRef.current?.scrollToOffset({ offset: 0, animated: false });
    },
    [fetchData, navigation],
  );

  // --- SEARCH HEADER COMPONENT ---
  const SearchHeader = useCallback(
    () => (
      <View style={[styles.headerContainer, { paddingTop: insets.top }]}>
        <SearchBar initialValue={searchTerm} onSearch={handleSearchSubmit} />

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
            : `Resultados para "${searchTerm}"`}
        </Text>
      </View>
    ),
    [insets, searchTerm, selectedMarket, handleSearchSubmit],
  );

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
    return <EmptySearchState query={searchTerm} />;
  };

  return (
    <View style={styles.container}>
      <ProductGrid
        products={products}
        onEndReached={() => fetchData()}
        onEndReachedThreshold={0.5}
        listFooterComponent={renderFooter()}
        listHeaderComponent={<SearchHeader />}
        listEmptyComponent={renderEmpty()}
        listRef={listRef}
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
