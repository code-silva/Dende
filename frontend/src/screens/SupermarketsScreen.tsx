import {
  type NavigationProp,
  type ParamListBase,
  useNavigation,
} from "@react-navigation/native";
import type * as Location from "expo-location";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { ActivityIndicator, StyleSheet, Text, View } from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { fetchSupermarkets } from "../api/markets";
import { MarketList } from "../components/MarketList";
import { SearchBar } from "../components/SearchBar";
import type { Market } from "../types/market";
import { searchMarkets } from "../utils/fuzzySearch";

const SEARCH_DEBOUNCE_MS = 500;

const RECOMMENDATION_RADIUS_KM = 10;
const SEARCH_RADIUS_KM = 30;

interface SupermarketsScreenProps {
  location: Location.LocationObject | null;
}

export function SupermarketsScreen({ location }: SupermarketsScreenProps) {
  const insets = useSafeAreaInsets();
  const navigation = useNavigation<NavigationProp<ParamListBase>>();
  const [markets, setMarkets] = useState<Market[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isSearching, setIsSearching] = useState(false);
  const [searchText, setSearchText] = useState("");
  // biome-ignore lint/correctness/noUnusedVariables: setter will be used when region filter UI is implemented
  const [selectedRegion, setSelectedRegion] = useState<string | null>(null);
  const abortControllerRef = useRef<AbortController | null>(null);

  const searchTextRef = useRef(searchText);
  searchTextRef.current = searchText;
  const selectedRegionRef = useRef(selectedRegion);
  selectedRegionRef.current = selectedRegion;

  const fetchSupermarketsData = useCallback(
    async (address?: string, city?: string | null, silent?: boolean) => {
      if (!location) return;

      abortControllerRef.current?.abort();
      const controller = new AbortController();
      abortControllerRef.current = controller;

      if (!silent) {
        const hasActiveSearch = !!address?.trim();
        if (hasActiveSearch) {
          setIsSearching(true);
        } else {
          setIsLoading(true);
        }
      }

      try {
        const radiusInKm = address?.trim()
          ? SEARCH_RADIUS_KM
          : RECOMMENDATION_RADIUS_KM;
        const data = await fetchSupermarkets(
          location.coords.latitude,
          location.coords.longitude,
          address,
          city,
          radiusInKm,
          controller.signal,
        );

        if (!controller.signal.aborted) {
          setMarkets(data);
        }
      } catch (error) {
        if (controller.signal.aborted) return;
        console.error("Erro ao buscar mercados:", error);
        setMarkets([]);
      } finally {
        setIsLoading(false);
        setIsSearching(false);
      }
    },
    [location],
  );

  useEffect(() => {
    fetchSupermarketsData(searchTextRef.current || undefined, selectedRegion);
  }, [fetchSupermarketsData, selectedRegion]);

  // biome-ignore lint/correctness/useExhaustiveDependencies: fetchSupermarketsData is stable (useCallback); selectedRegion read from ref to avoid triggering on region change (handled by Effect 1)
  useEffect(() => {
    const currentSearch = searchTextRef.current;

    if (!currentSearch.trim()) {
      fetchSupermarketsData(undefined, selectedRegionRef.current, true);
      return;
    }

    setIsSearching(true);
    const timer = setTimeout(() => {
      fetchSupermarketsData(currentSearch, selectedRegionRef.current);
    }, SEARCH_DEBOUNCE_MS);

    return () => {
      clearTimeout(timer);
      setIsSearching(false);
    };
  }, [searchText]);

  const filteredMarkets = useMemo(() => {
    let result = markets;

    if (selectedRegion) {
      const regionLower = selectedRegion.toLowerCase();
      result = result.filter(
        (m) =>
          m.city.toLowerCase() === regionLower ||
          m.state.toLowerCase() === regionLower,
      );
    }

    return searchMarkets(result, searchText);
  }, [markets, searchText, selectedRegion]);

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
          onChangeText={setSearchText}
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
              {isSearching
                ? "Buscando mercados..."
                : "Nenhum mercado com ofertas encontrado nesta região."}
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
