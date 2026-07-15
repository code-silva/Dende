import { Feather } from "@expo/vector-icons";
import MaterialCommunityIcons from "@expo/vector-icons/MaterialCommunityIcons";
import MaterialIcons from "@expo/vector-icons/MaterialIcons";
import type { BottomTabBarButtonProps } from "@react-navigation/bottom-tabs";
import { createBottomTabNavigator } from "@react-navigation/bottom-tabs";
import { createNativeStackNavigator } from "@react-navigation/native-stack";
import type * as Location from "expo-location";
import { useCallback } from "react";
import { StyleSheet, TouchableOpacity, View } from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { HomeScreen } from "../screens/HomeScreen";
import { MyListScreen } from "../screens/MyListScreen";
import { SearchResultsScreen } from "../screens/SearchResultsScreen";
import { StoreProductsScreen } from "../screens/StoreProductsScreen";
import { SupermarketsScreen } from "../screens/SupermarketsScreen";

const routeSettings = {
  home: {
    label: "INÍCIO",
    icon: "home",
    background: "rgba(16, 185, 129, 0.25)",
    color: "rgb(46, 177, 185)",
  },
  supermarkets: {
    label: "MERCADOS",
    icon: "shopping-bag",
    background: "rgba(46, 177, 185, 0.25)",
    color: "rgb(46, 177, 185)",
  },
  myList: {
    label: "MINHA LISTA",
    icon: "list",
    background: "rgba(46, 177, 185, 0.25)",
    color: "rgb(46, 177, 185)",
  },
};

const inactiveColor = "#44475C";
const Tab = createBottomTabNavigator();

function CustomTabButton(
  props: BottomTabBarButtonProps & {
    route: { name: string };
    isFocused: boolean;
  },
) {
  const { route, children, onPress, isFocused } = props;
  const settings = routeSettings[route.name];

  return (
    <TouchableOpacity
      onPress={onPress}
      style={styles.tabButtonContainer}
      activeOpacity={0.8}
    >
      <View
        style={[
          styles.pill,
          isFocused && { backgroundColor: settings.background },
        ]}
      >
        {children}
      </View>
    </TouchableOpacity>
  );
}

const HomeStack = createNativeStackNavigator();

function HomeStackScreen({
  location,
}: {
  location: Location.LocationObject | null;
}) {
  return (
    <HomeStack.Navigator id="homeStack" screenOptions={{ headerShown: false }}>
      <HomeStack.Screen name="HomeScreen">
        {() => <HomeScreen location={location} />}
      </HomeStack.Screen>

      <HomeStack.Screen
        name="SearchResultsScreen"
        component={SearchResultsScreen}
      />

      <HomeStack.Screen
        name="StoreProductsScreen"
        component={StoreProductsScreen}
      />
    </HomeStack.Navigator>
  );
}

const SupermarketStack = createNativeStackNavigator();

function SupermarketStackScreen({
  location,
}: {
  location: Location.LocationObject | null;
}) {
  return (
    <SupermarketStack.Navigator
      id="supermarketStack"
      screenOptions={{ headerShown: false }}
    >
      <SupermarketStack.Screen name="SupermarketsList">
        {() => <SupermarketsScreen location={location} />}
      </SupermarketStack.Screen>

      <SupermarketStack.Screen
        name="StoreProductsScreen"
        component={StoreProductsScreen}
      />
    </SupermarketStack.Navigator>
  );
}

export function BottomNavbar({
  location,
}: {
  location: Location.LocationObject | null;
}) {
  const insets = useSafeAreaInsets();

  const HomeScreenWrapper = useCallback(
    function HomeScreenWrapper() {
      return <HomeStackScreen location={location} />;
    },
    [location],
  );

  const SupermarketScreenWrapper = useCallback(
    function SupermarketScreenWrapper() {
      return <SupermarketStackScreen location={location} />;
    },
    [location],
  );

  return (
    <Tab.Navigator
      id="bottom_tabs"
      screenOptions={({ route, navigation }) => {
        const state = navigation.getState();
        const isFocused = state?.routes[state.index]?.name === route.name;

        return {
          headerShown: false,
          tabBarInactiveTintColor: inactiveColor,
          tabBarActiveTintColor: routeSettings[route.name]?.color,

          tabBarStyle: {
            ...styles.tabBar,
            height: 65 + insets.bottom,
            paddingBottom: insets.bottom > 0 ? insets.bottom : 10,
          },

          tabBarButton: (props) => (
            <CustomTabButton {...props} route={route} isFocused={isFocused} />
          ),
          tabBarLabelStyle: {
            fontSize: 12,
            fontWeight: "bold",
          },
        };
      }}
    >
      <Tab.Screen
        name="home"
        component={HomeScreenWrapper}
        options={{
          tabBarLabel: "INÍCIO",
          tabBarIcon: ({ color }) => (
            <Feather name="home" size={25} color={color} />
          ),
        }}
      />

      <Tab.Screen
        name="supermarkets"
        component={SupermarketScreenWrapper}
        options={{
          tabBarLabel: "MERCADOS",
          tabBarIcon: ({ color }) => (
            <MaterialCommunityIcons
              name="storefront-outline"
              size={25}
              color={color}
            />
          ),
        }}
      />

      <Tab.Screen
        name="myList"
        component={MyListScreen}
        options={{
          tabBarLabel: "MINHA LISTA",
          tabBarIcon: ({ color }) => (
            <MaterialIcons name="checklist" size={25} color={color} />
          ),
        }}
      />
    </Tab.Navigator>
  );
}

const styles = StyleSheet.create({
  tabBar: {
    borderTopWidth: 0,
    backgroundColor: "#FFF",
    shadowOffset: { width: 0, height: -8 },
    shadowOpacity: 0.1,
    shadowRadius: 20,
    elevation: 20,
  },
  tabButtonContainer: {
    flex: 1,
    justifyContent: "center",
    alignItems: "center",
    marginHorizontal: 4,
  },
  pill: {
    paddingVertical: 4,
    paddingHorizontal: 12,
    borderRadius: 20,
    overflow: "hidden",
    alignItems: "center",
    justifyContent: "center",
    minWidth: 85,
    height: 50,
  },
});
