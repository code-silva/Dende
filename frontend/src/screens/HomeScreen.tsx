import {
  type NavigationProp,
  type ParamListBase,
  useNavigation,
} from "@react-navigation/native";
import type * as Location from "expo-location";
import { memo, useCallback, useEffect, useState } from "react";
import { StyleSheet, View } from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { fetchMarkets } from "../api/markets";
import { EmptyProductState } from "../components/EmptyProductState";
import { HomeHeader } from "../components/HomeScreenHeader";
import { LoadingFooter } from "../components/LoadingFooter";
import { ProductGrid } from "../components/ProductGrid";
import { useProductsFetch } from "../hooks/useProductsFetch";
import type { Market } from "../types/market";
import type { Product } from "../types/product";

// SUPPORT FUNCTIONS

export const HomeScreen = memo(function HomeScreen({
  location,
}: {
  location: Location.LocationObject;
}) {
  const insets = useSafeAreaInsets();
  const [markets, setMarkets] = useState<Market[]>([]);
  const navigation = useNavigation<NavigationProp<ParamListBase>>();
  const { products, isLoading, hasMoreData, fetchData } = useProductsFetch({
    latitude: location?.coords.latitude,
    longitude: location?.coords.longitude,
  });

  const handlePress = useCallback((_product: Product) => {
    // TODO: navigate to product detail screen
  }, []);

  const handleAdd = useCallback((_product: Product) => {
    // TODO: add to persistent shopping list
  }, []);

  // NAVIGATION TO SPECIFIC MARKET SCREEN
  const handleMarketPress = useCallback(
    (market: Market) => {
      navigation.navigate("StoreProductsScreen", {
        selectedMarket: {
          id: market.id,
          name: market.name,
        },
        latitude: location?.coords.latitude,
        longitude: location?.coords.longitude,
      });
    },
    [location, navigation],
  );

  // EFFECTS

  // biome-ignore lint/correctness/useExhaustiveDependencies: initial fetch on mount
  useEffect(() => {
    if (location) {
      fetchData();
    }
  }, [location]);

  useEffect(() => {
    async function loadMarkets() {
      if (!location) return;

      const data = await fetchMarkets(
        location.coords.latitude,
        location.coords.longitude,
      );

      setMarkets(data);
    }

    loadMarkets();
  }, [location]);

  const renderFooter = () => {
    if (isLoading && products.length > 0) {
      return <LoadingFooter isLoading={isLoading} />;
    }

    if (!isLoading && products.length === 0 && !hasMoreData) {
      return <EmptyProductState isSearchEmpty={true} />;
    }

    if (!isLoading && !hasMoreData && products.length > 0) {
      return <EmptyProductState isSearchEmpty={false} />;
    }

    return null;
  };

  return (
    <View style={{ flex: 1, backgroundColor: "#FFF", paddingTop: insets.top }}>
      <ProductGrid
        products={products}
        handlePress={handlePress}
        handleAddToList={handleAdd}
        onEndReached={fetchData}
        onEndReachedThreshold={0.7}
        listFooterComponent={renderFooter()}
        listHeaderComponent={
          <HomeHeader markets={markets} handleMarketPress={handleMarketPress} />
        }
        contentContainerStyle={[
          styles.gridContainer,
          { paddingBottom: insets.bottom + 5 },
        ]}
      />
    </View>
  );
});

export const styles = StyleSheet.create({
  gridContainer: {
    paddingHorizontal: 14,
    flexGrow: 1,
  },
});
