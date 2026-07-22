import AsyncStorage from "@react-native-async-storage/async-storage";
import { NavigationContainer } from "@react-navigation/native";
import { createNativeStackNavigator } from "@react-navigation/native-stack";
import * as Location from "expo-location";
import * as SplashScreen from "expo-splash-screen";
import { useEffect, useState } from "react";
import { SafeAreaProvider } from "react-native-safe-area-context";
import { BottomNavbar } from "./src/components/BottomNavbar";
// Hooks and Screens
import { useLoadFonts } from "./src/hooks/useLoadFonts";
import { OnboardingLocal } from "./src/screens/OnboardingScreen";
import Splash from "./src/screens/SplashScreen";
// Pre-fetching API and global store
import {
  fetchHomeHighlights,
  fetchMyListInitialState,
  fetchNearbyMarkets,
} from "./src/api/api";
import { useAppStore } from "./src/store/useAppStore";

// Prevent the splash screen from hiding automatically while fonts load
SplashScreen.preventAutoHideAsync();

const Stack = createNativeStackNavigator();

export default function App() {
  const { fontsLoaded } = useLoadFonts();
  const [location, setLocation] = useState<Location.LocationObject | null>(
    null,
  );
  const [triedToGetLocation, setTriedToGetLocation] = useState(false);
  const [showOnboarding, setShowOnboarding] = useState<boolean | null>(null);
  const [isSplashFinished, setIsSplashFinished] = useState(false);

  const setMarkets = useAppStore((state) => state.setMarkets);
  const setHomeHighlights = useAppStore((state) => state.setHomeHighlights);
  const setMyList = useAppStore((state) => state.setMyList);
  const setInitialDataLoaded = useAppStore(
    (state) => state.setInitialDataLoaded,
  );

  // Hide native splash screen as soon as fonts are loaded
  useEffect(() => {
    if (fontsLoaded) {
      SplashScreen.hideAsync();
    }
  }, [fontsLoaded]);

  // Obtaining user's location, pre-fetching data, and checking onboarding status
  useEffect(() => {
    async function initializeApp() {
      let latitude: number | undefined;
      let longitude: number | undefined;

      // Location request
      const { status } = await Location.requestForegroundPermissionsAsync();
      if (status === "granted") {
        const currentLocation = await Location.getCurrentPositionAsync({
          accuracy: Location.Accuracy.Highest,
        });
        setLocation(currentLocation);
        latitude = currentLocation.coords.latitude;
        longitude = currentLocation.coords.longitude;
      }
      setTriedToGetLocation(true);

      // Pre-fetch data in parallel
      try {
        const [markets, highlights, myList] = await Promise.all([
          fetchNearbyMarkets(latitude, longitude),
          fetchHomeHighlights(latitude, longitude),
          fetchMyListInitialState(),
        ]);

        setMarkets(markets);
        setHomeHighlights(highlights?.results ?? []);
        setMyList(myList);
      } catch (error) {
        console.error("Error during pre-fetch:", error);
      } finally {
        setInitialDataLoaded(true);
      }

      // Onboarding check
      try {
        const hasSeenOnboarding =
          await AsyncStorage.getItem("hasSeenOnboarding");
        setShowOnboarding(hasSeenOnboarding !== "true");
      } catch (error) {
        console.error("Error checking onboarding status:", error);
        setShowOnboarding(false);
      }
    }

    initializeApp();
  }, []);

  if (!fontsLoaded) {
    return null;
  }

  if (!isSplashFinished) {
    return <Splash onAnimationEnd={() => setIsSplashFinished(true)} />;
  }

  return (
    <SafeAreaProvider>
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
    </SafeAreaProvider>
  );
}
