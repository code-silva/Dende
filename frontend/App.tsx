import AsyncStorage from "@react-native-async-storage/async-storage";
import { NavigationContainer } from "@react-navigation/native";
import { createNativeStackNavigator } from "@react-navigation/native-stack";
import * as Location from "expo-location";
import * as SplashScreen from "expo-splash-screen";
import { useCallback, useEffect, useRef, useState } from "react";
import { StyleSheet, View } from "react-native";
import { SafeAreaProvider } from "react-native-safe-area-context";
import {
  fetchHomeHighlights,
  fetchMyListInitialState,
  fetchNearbyMarkets,
} from "./src/api/api";
import { BottomNavbar } from "./src/components/BottomNavbar";
import { useLoadFonts } from "./src/hooks/useLoadFonts";
import { OnboardingLocal } from "./src/screens/OnboardingScreen";
import Splash from "./src/screens/SplashScreen";
import { useAppStore } from "./src/store/useAppStore";

SplashScreen.preventAutoHideAsync();

const Stack = createNativeStackNavigator();

export default function App() {
  const { fontsLoaded } = useLoadFonts();
  const [location, setLocation] = useState<Location.LocationObject | null>(
    null,
  );
  const [showOnboarding, setShowOnboarding] = useState<boolean | null>(null);
  const [animationEnded, setAnimationEnded] = useState(false);
  const [dataReady, setDataReady] = useState(false);
  const [dataError, setDataError] = useState<string | null>(null);
  const [isSplashFinished, setIsSplashFinished] = useState(false);
  const [isNavigable, setIsNavigable] = useState(false);

  const setMarkets = useAppStore((state) => state.setMarkets);
  const setHomeHighlights = useAppStore((state) => state.setHomeHighlights);
  const setMyList = useAppStore((state) => state.setMyList);
  const setInitialDataLoaded = useAppStore(
    (state) => state.setInitialDataLoaded,
  );
  const setPreFetchError = useAppStore((state) => state.setPreFetchError);
  const setIsRetrying = useAppStore((state) => state.setIsRetrying);

  const abortRef = useRef<AbortController | null>(null);

  useEffect(() => {
    if (fontsLoaded) {
      SplashScreen.hideAsync();
    }
  }, [fontsLoaded]);

  useEffect(() => {
    AsyncStorage.getItem("hasSeenOnboarding")
      .then((val) => setShowOnboarding(val !== "true"))
      .catch(() => setShowOnboarding(false));
  }, []);

  useEffect(() => {
    if (fontsLoaded && showOnboarding !== null) {
      setIsNavigable(true);
    }
  }, [fontsLoaded, showOnboarding]);

  const runPreFetch = useCallback(async () => {
    abortRef.current?.abort();
    const controller = new AbortController();
    abortRef.current = controller;

    setDataError(null);
    setDataReady(false);
    setPreFetchError(null);

    let latitude: number | undefined;
    let longitude: number | undefined;

    try {
      const { status } = await Location.requestForegroundPermissionsAsync();
      if (status === "granted" && !controller.signal.aborted) {
        const currentLocation = await Location.getCurrentPositionAsync({
          accuracy: Location.Accuracy.Highest,
        });
        setLocation(currentLocation);
        latitude = currentLocation.coords.latitude;
        longitude = currentLocation.coords.longitude;
      }
    } catch {
      // location permission denied — proceed with undefined coords
    }

    if (controller.signal.aborted) return;

    try {
      const [markets, highlights, myList] = await Promise.all([
        fetchNearbyMarkets(latitude, longitude, controller.signal),
        fetchHomeHighlights(latitude, longitude, controller.signal),
        fetchMyListInitialState(),
      ]);

      if (controller.signal.aborted) return;

      setMarkets(markets);
      setHomeHighlights(highlights?.results ?? []);
      setMyList(myList);
      setDataReady(true);
      setInitialDataLoaded(true);
    } catch {
      if (controller.signal.aborted) return;
      setDataError(
        "🌐 Parece que você está sem internet. Verifique sua conexão para carregar as melhores ofertas do Dendê!",
      );
      setPreFetchError(
        "🌐 Parece que você está sem internet. Verifique sua conexão para carregar as melhores ofertas do Dendê!",
      );
    } finally {
      if (!controller.signal.aborted) {
        setInitialDataLoaded(true);
      }
    }
  }, [
    setMarkets,
    setHomeHighlights,
    setMyList,
    setInitialDataLoaded,
    setPreFetchError,
  ]);

  useEffect(() => {
    runPreFetch();
    return () => abortRef.current?.abort();
  }, [runPreFetch]);

  const handleAnimationEnd = useCallback(() => {
    setAnimationEnded(true);
  }, []);

  const handleRetry = useCallback(() => {
    setIsRetrying(true);
    runPreFetch().finally(() => setIsRetrying(false));
  }, [runPreFetch, setIsRetrying]);

  useEffect(() => {
    if (animationEnded && dataReady) {
      setIsSplashFinished(true);
    }
  }, [animationEnded, dataReady]);

  if (!isNavigable) {
    return null;
  }

  return (
    <SafeAreaProvider>
      <View style={styles.root}>
        <NavigationContainer>
          <Stack.Navigator
            id="rootStack"
            initialRouteName={showOnboarding ? "OnboardingLocal" : "MainTabs"}
            screenOptions={{
              headerShown: false,
              animation: "slide_from_right",
            }}
          >
            {showOnboarding && (
              <Stack.Screen name="OnboardingLocal">
                {(props) => <OnboardingLocal {...props} />}
              </Stack.Screen>
            )}
            <Stack.Screen name="MainTabs">
              {(props) => <BottomNavbar {...props} location={location} />}
            </Stack.Screen>
          </Stack.Navigator>
        </NavigationContainer>

        {!isSplashFinished && (
          <View style={styles.splashOverlay} pointerEvents="auto">
            <Splash
              onAnimationEnd={handleAnimationEnd}
              error={dataError}
              onRetry={handleRetry}
            />
          </View>
        )}
      </View>
    </SafeAreaProvider>
  );
}

const styles = StyleSheet.create({
  root: {
    flex: 1,
  },
  splashOverlay: {
    ...StyleSheet.absoluteFillObject,
  },
});
