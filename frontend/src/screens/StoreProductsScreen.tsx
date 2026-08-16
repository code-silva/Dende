import { useCallback, useEffect, useRef, useState } from "react";
import { Keyboard, StyleSheet, View } from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { AiInfoBanner } from "../components/AiInfoBanner";
import { EmptyProductState } from "../components/EmptyProductState";
import { EmptySearchState } from "../components/EmptySearchState";
import { LoadingFooter } from "../components/LoadingFooter";
import { MarketBanner } from "../components/MarketBanner";
import { ProductGrid } from "../components/ProductGrid";
import { SearchBar } from "../components/SearchBar";
import { useProductsFetch } from "../hooks/useProductsFetch";
import type { Product } from "../types/product";

interface StoreProductsScreenProps {
  route: {
    params: {
      selectedMarket: { id: number; name: string };
      latitude?: number;
      longitude?: number;
    };
  };
}

export function StoreProductsScreen({ route }: StoreProductsScreenProps) {
  const insets = useSafeAreaInsets();
  const { selectedMarket, latitude, longitude } = route.params;
  const actualName: string = selectedMarket?.name || "";
  const displayName: string = actualName.toUpperCase();
  const [searchTerm, setSearchTerm] = useState("");
  const { products, isLoading, hasMoreData, fetchData } = useProductsFetch({
    latitude,
    longitude,
    marketId: selectedMarket?.id,
    query: searchTerm.trim() || undefined,
  });

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
      setSearchTerm(trimmed);
      fetchData(trimmed, true);
    },
    [fetchData],
  );

  const handleDebouncedChange = useCallback(
    (text: string) => {
      const trimmed = text.trim();
      setSearchTerm(trimmed);
      fetchData(trimmed, true);
    },
    [fetchData],
  );

  const headerElement = (
    <View style={styles.headerContainer}>
      <MarketBanner
        marketName={displayName}
        subtitle="OFERTAS DESTA UNIDADE"
      ></MarketBanner>

      <View style={styles.aiBannerWrapper}>
        <AiInfoBanner />
      </View>
    </View>
  );

  const isSearchEmpty =
    searchTerm.trim() !== "" && !isLoading && products.length === 0;

  const renderFooter = () => {
    if (isLoading && products.length > 0) {
      return <LoadingFooter isLoading={isLoading} />;
    }
    if (!isLoading && !hasMoreData && products.length > 0) {
      return <EmptyProductState isSearchEmpty={false} />;
    }
    return null;
  };

  const listEmptyComponent = isSearchEmpty ? (
    <EmptySearchState query={searchTerm} />
  ) : (
    <EmptyProductState isSearchEmpty={false} />
  );

  return (
    <View
      style={{
        flex: 1,
        backgroundColor: "#FFF",
        paddingTop: insets.top,
      }}
    >
      <View
        style={{
          zIndex: 10,
          backgroundColor: "#FFF",
          paddingHorizontal: 14,
          paddingBottom: 10,
        }}
      >
        <SearchBar
          placeholder={`Buscar em ${actualName || "mercado"}...`}
          inputStyle={{ fontSize: 14 }}
          onSearch={handleSearchSubmit}
          onDebouncedChange={handleDebouncedChange}
          disableApiSearch
        />
      </View>

      {isLoading && products.length === 0 ? (
        <View style={styles.centered}>
          <LoadingFooter
            isLoading
            message={
              searchTerm.trim()
                ? "Buscando produtos..."
                : "Carregando ofertas..."
            }
          />
        </View>
      ) : (
        <ProductGrid
          products={products}
          handlePress={handleProductPress}
          handleAddToList={handleAddToList}
          onEndReached={() => fetchData()}
          onEndReachedThreshold={0.7}
          listHeaderComponent={headerElement}
          listFooterComponent={renderFooter()}
          listEmptyComponent={listEmptyComponent}
          contentContainerStyle={styles.gridContainer}
        />
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  headerContainer: {
    width: "100%",
    paddingBottom: 10,
  },
  aiBannerWrapper: {
    marginBottom: 12,
  },
  centered: {
    flex: 1,
    justifyContent: "center",
    alignItems: "center",
    paddingHorizontal: 32,
  },
  gridContainer: {
    paddingHorizontal: 14,
    flexGrow: 1,
  },
});
