import { FontAwesome5, MaterialCommunityIcons } from "@expo/vector-icons";
import React, { memo } from "react";
import {
  Dimensions,
  Image,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from "react-native";
import type { Product } from "../types/product";

interface ProductCardProps {
  product: Product;
  ranking?: number;
  handlePress?: (product: Product) => void;
  handleAddToList?: (product: Product) => void;
}

const ProductCard: React.FC<ProductCardProps> = ({
  product,
  ranking,
  handlePress,
  handleAddToList,
}) => {
  const screenWidth = Dimensions.get("window").width;
  const isSmallDevice = screenWidth < 360;

  const formattedDistance = React.useMemo(() => {
    if (product.distanceInKilometers === undefined) return null;
    if (product.distanceInKilometers === null) return null;

    const value = Number(product.distanceInKilometers);
    if (value < 1) {
      return `${Math.ceil(value * 1000)} m`;
    }
    return `${value.toFixed(1)} km`;
  }, [product.distanceInKilometers]);

  return (
    <TouchableOpacity
      style={[styles.card, { padding: isSmallDevice ? 8 : 12 }]}
      onPress={handlePress ? () => handlePress(product) : undefined}
      activeOpacity={0.9}
    >
      <View style={styles.imageContainer}>
        <Image
          source={{ uri: product.image || "https://via.placeholder.com/150" }}
          style={styles.productImage}
          resizeMode="contain"
        />

        <View style={styles.rankingBadge}>
          <Text style={styles.rankingText}>#{ranking || product.id}</Text>
        </View>

        <View style={styles.priceLabel}>
          <Text
            style={[styles.priceText, { fontSize: isSmallDevice ? 10 : 11 }]}
          >
            R$ {Number(product.price).toFixed(2).replace(".", ",")}
          </Text>
        </View>

        {handleAddToList && (
          <TouchableOpacity
            style={[
              styles.addButton,
              {
                width: isSmallDevice ? 26 : 30,
                height: isSmallDevice ? 26 : 30,
                borderRadius: isSmallDevice ? 13 : 15,
              },
            ]}
            onPress={() => handleAddToList(product)}
          >
            <MaterialCommunityIcons
              name="playlist-plus"
              size={isSmallDevice ? 16 : 18}
              color="#28a8b5"
            />
          </TouchableOpacity>
        )}
      </View>

      <View style={styles.infoContainer}>
        <View style={styles.topInfoRow}>
          <View style={styles.productNameWrapper}>
            <Text
              style={styles.productName}
              numberOfLines={2}
              ellipsizeMode="tail"
            >
              {product.productName}
              {product.measurement
                ? ` | ${Math.floor(Number(product.measurement))} ${product.measurementUnit || ""}`
                : product.measurementUnit
                  ? ` | ${product.measurementUnit}`
                  : ""}
            </Text>
          </View>

          <View style={styles.marketWrapper}>
            <Text style={styles.marketName} numberOfLines={1}>
              {product.marketName}
            </Text>
          </View>
        </View>

        <View style={styles.bottomInfoRow}>
          <Text style={styles.brandStyle} numberOfLines={1}>
            {product.brand}
          </Text>

          {formattedDistance && (
            <View style={styles.distanceWrapper}>
              <View style={styles.iconContainer}>
                <FontAwesome5 name="walking" size={8} color="#999" />
                <View style={styles.dashLine} />
                <FontAwesome5 name="map-marker-alt" size={8} color="#999" />
              </View>
              <Text style={styles.distanceText}>{formattedDistance}</Text>
            </View>
          )}
        </View>
      </View>
    </TouchableOpacity>
  );
};

const styles = StyleSheet.create({
  card: {
    backgroundColor: "#fff",
    borderRadius: 18,
    padding: 10,
    elevation: 4,
  },
  imageContainer: {
    width: "100%",
    aspectRatio: 1,
    position: "relative",
    overflow: "hidden",
    borderRadius: 12,
    marginBottom: 8,
    backgroundColor: "#f9f9f9",
    justifyContent: "center",
    alignItems: "center",
  },
  productImage: {
    width: "85%",
    height: "85%",
  },
  productName: {
    fontWeight: "700",
    fontSize: 11,
    lineHeight: 18,
    color: "#333",
  },
  marketName: {
    fontSize: 10,
    fontWeight: "600",
    color: "#28a8b5",
    textAlign: "right",
  },
  marketWrapper: {
    flex: 0.7,
    alignItems: "flex-end",
    justifyContent: "center",
    height: 38,
  },
  rankingBadge: {
    position: "absolute",
    top: 8,
    left: 8,
    backgroundColor: "rgba(255, 255, 255, 0.9)",
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 6,
    borderWidth: 1,
    borderColor: "#eee",
  },
  rankingText: {
    fontSize: 10,
    color: "#888",
    fontWeight: "bold",
  },
  priceLabel: {
    minWidth: 30,
    paddingHorizontal: 6,
    paddingVertical: 3,
    backgroundColor: "#28a8b5",
    borderRadius: 6,
    position: "absolute",
    top: 8,
    right: 8,
  },
  priceText: {
    color: "#ffffff",
    fontWeight: "800",
    fontSize: 12,
  },
  addButton: {
    position: "absolute",
    bottom: 10,
    alignSelf: "center",
    borderRadius: 5,
    backgroundColor: "#FFFFFF",
    justifyContent: "center",
    alignItems: "center",
    elevation: 4,
  },
  infoContainer: {
    paddingVertical: 2,
    gap: 2,
  },
  topInfoRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "flex-start",
  },
  bottomInfoRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "flex-end",
    marginTop: 2,
    height: 26,
  },
  productNameWrapper: {
    flex: 1.3,
    paddingRight: 10,
    height: 38,
    justifyContent: "center",
  },
  brandStyle: {
    fontSize: 10,
    color: "#888",
    textTransform: "uppercase",
  },
  distanceWrapper: {
    alignItems: "flex-end",
    justifyContent: "center",
    flexDirection: "column",
  },
  iconContainer: {
    flexDirection: "row",
    alignItems: "center",
    marginBottom: 2,
  },
  dashLine: {
    width: 8,
    height: 1,
    backgroundColor: "#999",
    marginHorizontal: 3,
  },
  distanceText: {
    fontSize: 10,
    color: "#999",
    fontWeight: "600",
    textAlign: "right",
  },
});

export default memo(ProductCard);
