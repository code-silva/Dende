import {
  type NavigationProp,
  type ParamListBase,
  useNavigation,
} from "@react-navigation/native";
import * as Location from "expo-location";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { ActivityIndicator, StyleSheet, Text, View } from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { fetchCities } from "../api/cities";
import { fetchSupermarkets } from "../api/markets";
import { CityFilter } from "../components/CityFilter";
import { LoadingFooter } from "../components/LoadingFooter";
import { MarketList } from "../components/MarketList";
import { SearchBar } from "../components/SearchBar";
import type { Market } from "../types/market";
import { normalizeString, searchMarkets } from "../utils/fuzzySearch";

const SEARCH_DEBOUNCE_MS = 500;

interface SupermarketsScreenProps {
  location: Location.LocationObject | null;
}

export function SupermarketsScreen({ location }: SupermarketsScreenProps) {
  const insets = useSafeAreaInsets();
  const navigation = useNavigation<NavigationProp<ParamListBase>>();
  const [markets, setMarkets] = useState<Market[]>([]);
  const [cities, setCities] = useState<string[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isSearching, setIsSearching] = useState(false);
  const [searchText, setSearchText] = useState("");
  const [selectedCity, setSelectedCity] = useState<string | null>(null);
  const abortControllerRef = useRef<AbortController | null>(null);
  const debounceTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const searchTextRef = useRef(searchText);
  searchTextRef.current = searchText;
  const selectedCityRef = useRef(selectedCity);
  selectedCityRef.current = selectedCity;

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
        const data = await fetchSupermarkets(
          location.coords.latitude,
          location.coords.longitude,
          address,
          city,
          undefined,
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
        if (!controller.signal.aborted) {
          setIsLoading(false);
          setIsSearching(false);
        }
      }
    },
    [location],
  );

  useEffect(() => {
    fetchSupermarketsData(searchTextRef.current || undefined, selectedCity);
  }, [fetchSupermarketsData, selectedCity]);

  useEffect(() => {
    let cancelled = false;
    fetchCities()
      .then((data) => {
        if (!cancelled) setCities(data);
      })
      .catch(() => {
        if (!cancelled) setCities([]);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    if (!location) return;
    let cancelled = false;
    Location.reverseGeocodeAsync({
      latitude: location.coords.latitude,
      longitude: location.coords.longitude,
    })
      .then((addresses) => {
        if (cancelled) return;
        const geoCity = addresses?.[0]?.city;
        if (!geoCity) return;
        const normalized = normalizeString(geoCity);
        const match = cities.find(
          (city) => normalizeString(city) === normalized,
        );
        if (match) setSelectedCity(match);
      })
      .catch(() => {
        // reverse geocoding failed — keep no city filter
      });
    return () => {
      cancelled = true;
    };
  }, [location, cities]);

  // biome-ignore lint/correctness/useExhaustiveDependencies: fetchSupermarketsData is stable (useCallback); selectedCity read from ref to avoid triggering on city change (handled by Effect 1)
  useEffect(() => {
    const currentSearch = searchTextRef.current;

    if (!currentSearch.trim()) {
      setIsSearching(false);
      fetchSupermarketsData(undefined, selectedCityRef.current, true);
      return;
    }

    setIsSearching(true);
    debounceTimerRef.current = setTimeout(() => {
      fetchSupermarketsData(currentSearch, selectedCityRef.current, true);
    }, SEARCH_DEBOUNCE_MS);

    return () => {
      if (debounceTimerRef.current) {
        clearTimeout(debounceTimerRef.current);
        debounceTimerRef.current = null;
      }
    };
  }, [searchText]);

  const handleSearchSubmit = useCallback(
    (text: string) => {
      if (debounceTimerRef.current) {
        clearTimeout(debounceTimerRef.current);
        debounceTimerRef.current = null;
      }

      const trimmed = text.trim();
      if (!trimmed) {
        fetchSupermarketsData(undefined, selectedCityRef.current, true);
        return;
      }
      setSearchText(trimmed);
      fetchSupermarketsData(trimmed, selectedCityRef.current);
    },
    [fetchSupermarketsData],
  );

  const filteredMarkets = useMemo(
    () => searchMarkets(markets, searchText),
    [markets, searchText],
  );

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
          onSearch={handleSearchSubmit}
          disableApiSearch
        />
        <CityFilter
          cities={cities}
          selectedCity={selectedCity}
          onSelectCity={setSelectedCity}
        />
      </View>

      {isSearching ? (
        <View style={styles.centered}>
          <LoadingFooter isLoading message="Buscando mercados..." />
        </View>
      ) : (
        <MarketList
          markets={filteredMarkets}
          handleMarketPress={handleMarketPress}
          listHeaderComponent={listHeader}
          listEmptyComponent={
            <View style={styles.centered}>
              <Text style={styles.emptyText}>
                {selectedCity
                  ? "Sem mercados ativos nessa região."
                  : "Nenhum mercado com ofertas encontrado nesta região."}
              </Text>
            </View>
          }
        />
      )}
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
