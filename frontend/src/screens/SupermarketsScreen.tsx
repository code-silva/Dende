import {
  type NavigationProp,
  type ParamListBase,
  useNavigation,
} from "@react-navigation/native";
import type * as Location from "expo-location";
import { useCallback, useEffect, useMemo, useState } from "react";
import { ActivityIndicator, StyleSheet, Text, View } from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { fetchMarkets } from "../api/markets";
import { MarketList } from "../components/MarketList";
import { SearchBar } from "../components/SearchBar";
import type { Market } from "../types/market";

const DISTANCE_LIMIT_KM = 10;

interface SupermarketsScreenProps {
  location: Location.LocationObject | null;
}

export function SupermarketsScreen({ location }: SupermarketsScreenProps) {
  const insets = useSafeAreaInsets();
  const navigation = useNavigation<NavigationProp<ParamListBase>>();
  const [markets, setMarkets] = useState<Market[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");

  useEffect(() => {
    async function loadMarkets() {
      if (!location) return;

      setIsLoading(true);
      try {
        const data = await fetchMarkets(
          location.coords.latitude,
          location.coords.longitude,
        );

        const paginatedData = data as unknown as { results: Market[] };

        if (paginatedData && Array.isArray(paginatedData.results)) {
          setMarkets(paginatedData.results);
        } else {
          console.warn(
            "A estrutura da API mudou ou .results não é um array válido:",
            data,
          );
          setMarkets([]);
        }
      } catch (error) {
        console.error("Erro ao buscar mercados:", error);
        setMarkets([]);
      } finally {
        setIsLoading(false);
      }
    }

    loadMarkets();
  }, [location]);

  const validMarkets = useMemo(
    () =>
      markets
        .filter(
          (m) =>
            m.distanceInKilometers != null &&
            m.distanceInKilometers <= DISTANCE_LIMIT_KM,
        )
        .sort(
          (a, b) =>
            (a.distanceInKilometers ?? Infinity) -
            (b.distanceInKilometers ?? Infinity),
        ),
    [markets],
  );

  const filteredMarkets = useMemo(() => {
    const query = searchQuery.trim().toLowerCase();
    if (!query) return validMarkets;
    return validMarkets.filter((m) => m.name.toLowerCase().includes(query));
  }, [validMarkets, searchQuery]);

  const listHeader = useMemo(
    () => (
      <View style={styles.listHeader}>
        <Text style={styles.headerTitle}>Principais Escolhas</Text>
        <Text style={styles.headerSubtitle}>
          Mercados com ofertas ativas e com baixo preço na região.
        </Text>
      </View>
    ),
    [],
  );

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

  if (isLoading) {
    return (
      <View style={[styles.centered, { paddingTop: insets.top }]}>
        <ActivityIndicator size="large" color="#00838F" />
      </View>
    );
  }

  return (
    <View style={[styles.screen, { paddingTop: insets.top }]}>
      <View style={styles.searchWrapper}>
        <SearchBar
          placeholder="Buscar mercados..."
          onChangeText={setSearchQuery}
          disableApiSearch
        />
      </View>

      <MarketList
        markets={filteredMarkets}
        handleMarketPress={handleMarketPress}
        listHeaderComponent={listHeader}
        listEmptyComponent={
          <View style={styles.centered}>
            <Text style={styles.emptyText}>
              Nenhum mercado com ofertas encontrado nesta região.
            </Text>
          </View>
        }
      />
    </View>
  );
}

const styles = StyleSheet.create({
  screen: {
    flex: 1,
    backgroundColor: "#FFFFFF",
  },
  centered: {
    flex: 1,
    justifyContent: "center",
    alignItems: "center",
    paddingHorizontal: 32,
  },
  searchWrapper: {
    paddingHorizontal: 16,
  },
  listHeader: {
    paddingHorizontal: 16,
    marginTop: 4,
    marginBottom: 16,
  },
  headerTitle: {
    fontSize: 19,
    fontFamily: "Inter-Bold",
    color: "#333333",
    marginBottom: 4,
  },
  headerSubtitle: {
    fontSize: 14,
    fontFamily: "Inter-Regular",
    color: "#999999",
    lineHeight: 20,
  },
  emptyText: {
    fontSize: 15,
    fontFamily: "Inter-Regular",
    color: "#999999",
    textAlign: "center",
    lineHeight: 22,
  },
});
