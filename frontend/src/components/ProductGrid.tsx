import type React from "react";
import {
  FlatList,
  type StyleProp,
  StyleSheet,
  useWindowDimensions,
  View,
  type ViewStyle,
} from "react-native";
import type { Product } from "../types/product";
import ProductCard from "./ProductCard";

interface ProductGridProps {
  products: Product[];
  handlePress: (product: Product) => void;
  handleAddToList: (product: Product) => void;
  onEndReached?: () => void;
  onEndReachedThreshold?: number;
  listFooterComponent?: React.ReactElement | null;
  listHeaderComponent?: React.ReactElement | null;
  listEmptyComponent?: React.ReactElement | null;
  contentContainerStyle?: StyleProp<ViewStyle>;
}

const TABLET_LARGE = 1024;
const TABLET_STANDARD = 768;
const MOBILE_STANDARD = 320;

export const ProductGrid: React.FC<ProductGridProps> = ({
  products,
  handlePress,
  handleAddToList,
  onEndReached,
  onEndReachedThreshold,
  listFooterComponent,
  listHeaderComponent,
  listEmptyComponent,
  contentContainerStyle,
}) => {
  const { width } = useWindowDimensions();

  // This function calculates the number of columns for the grid based on the current screen width and predefined breakpoints. It ensures that the grid is responsive and adapts to different device sizes, providing an optimal layout for users on mobile, tablet, and larger screens.
  const getNumColumns = (): number => {
    if (width >= TABLET_LARGE) return 4;
    if (width >= TABLET_STANDARD) return 3;
    if (width >= MOBILE_STANDARD) return 2;
    return 1;
  };

  const numColumns = getNumColumns();

  return (
    <FlatList
      data={products}
      keyExtractor={(item, index) => `${item.id}-${index}`}
      renderItem={({ item, index }) => (
        <View
          style={
            numColumns > 1
              ? [styles.cardWrapper, { maxWidth: `${100 / numColumns}%` }]
              : { width: "100%", padding: 6 }
          }
        >
          <ProductCard
            product={item}
            ranking={index + 1}
            handlePress={handlePress}
            handleAddToList={handleAddToList}
          />
        </View>
      )}
      key={`grid-${numColumns}`}
      numColumns={numColumns}
      initialNumToRender={numColumns * 3}
      maxToRenderPerBatch={numColumns * 6}
      windowSize={9}
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
    padding: 6,
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
    padding: 6,
  },
});
