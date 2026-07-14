import type React from "react";
import {
  FlatList,
  type StyleProp,
  StyleSheet,
  useWindowDimensions,
  View,
  type ViewStyle,
} from "react-native";
import type { Market } from "../types/market";
import { MarketCard } from "./MarketCard";

interface MarketListProps {
  markets: Market[];
  handleMarketPress: (market: Market) => void;
  onEndReached?: () => void;
  onEndReachedThreshold?: number;
  listFooterComponent?: React.ReactElement | null;
  listHeaderComponent?: React.ReactElement | null;
  listEmptyComponent?: React.ReactElement | null;
  contentContainerStyle?: StyleProp<ViewStyle>;
}

// Breakpoints consistent with your design system
const DESKTOP_LARGE = 1200;
const TABLET_LANDSCAPE = 900;

export const MarketList: React.FC<MarketListProps> = ({
  markets,
  handleMarketPress,
  onEndReached,
  onEndReachedThreshold,
  listFooterComponent,
  listHeaderComponent,
  listEmptyComponent,
  contentContainerStyle,
}) => {
  const { width } = useWindowDimensions();

  // Dynamic columns definition for markets list
  const getNumColumns = (): number => {
    if (width >= DESKTOP_LARGE) return 3; // Monitors / Notebooks
    if (width >= TABLET_LANDSCAPE) return 2; // Tablets in landscape
    return 1; // Standard mobile screens
  };

  const numColumns = getNumColumns();

  return (
    <FlatList
      data={markets}
      // Re-render the grid correctly when changing orientations or resizing the window
      key={`market-grid-${numColumns}`}
      numColumns={numColumns}
      keyExtractor={(item, index) => `market-${item.id}-${index}`}
      renderItem={({ item }) => (
        <View
          style={
            numColumns > 1
              ? [styles.cardWrapper, { maxWidth: `${100 / numColumns}%` }]
              : styles.fullWidthWrapper
          }
        >
          <MarketCard market={item} onPress={() => handleMarketPress(item)} />
        </View>
      )}
      columnWrapperStyle={numColumns > 1 ? styles.rowWrapper : null}
      contentContainerStyle={[styles.listContainer, contentContainerStyle]}
      onEndReached={onEndReached}
      onEndReachedThreshold={onEndReachedThreshold}
      ListFooterComponent={listFooterComponent}
      ListHeaderComponent={listHeaderComponent}
      ListEmptyComponent={listEmptyComponent}
    />
  );
};

const styles = StyleSheet.create({
  listContainer: {
    paddingVertical: 16,
    paddingHorizontal: 8,
  },
  rowWrapper: {
    justifyContent: "flex-start",
    flexDirection: "row",
    width: "100%",
  },
  cardWrapper: {
    flexGrow: 1,
    flexShrink: 0,
    flexBasis: 0,
    padding: 8,
  },
  fullWidthWrapper: {
    width: "100%",
  },
});
