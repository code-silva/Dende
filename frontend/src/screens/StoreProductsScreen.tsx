import { useEffect } from "react";
import { StyleSheet, View } from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { EmptyProductState } from "../components/EmptyProductState";
import { LoadingFooter } from "../components/LoadingFooter";
import { MarketBanner } from "../components/MarketBanner";
import { ProductGrid } from "../components/ProductGrid";
import { SearchBar } from "../components/SearchBar";
import { useProductsFetch } from "../hooks/useProductsFetch";

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
  const { products, isLoading, hasMoreData, fetchData } = useProductsFetch({
    latitude,
    longitude,
    marketId: selectedMarket?.id,
  });

  // biome-ignore lint/correctness/useExhaustiveDependencies: initial fetch on mount
  useEffect(() => {
    fetchData();
  }, []);

  const headerElement = (
    <View style={styles.headerContainer}>
      <MarketBanner
        marketName={displayName}
        subtitle="OFERTAS DESTA UNIDADE"
      ></MarketBanner>
    </View>
  );

  const renderFooter = () => {
    if (isLoading) {
      return <LoadingFooter isLoading={isLoading} />;
    }
    if (!isLoading && products.length === 0 && !hasMoreData) {
      return <EmptyProductState />;
    }
    if (!isLoading && !hasMoreData && products.length > 0) {
      return <EmptyProductState />;
    }
    return null;
  };

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
        />
      </View>

      <ProductGrid
        products={products}
        handlePress={(product) =>
          console.log("Details for:", product.productName)
        }
        handleAddToList={(product) =>
          console.log("Add to List:", product.productName)
        }
        onEndReached={fetchData}
        onEndReachedThreshold={0.7}
        listHeaderComponent={headerElement}
        listFooterComponent={renderFooter()}
        contentContainerStyle={styles.gridContainer}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  headerContainer: {
    width: "100%",
    paddingBottom: 10,
  },
  gridContainer: {
    paddingHorizontal: 14,
    flexGrow: 1,
  },
});
