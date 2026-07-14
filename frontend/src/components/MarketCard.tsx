import { Ionicons } from "@expo/vector-icons";
import {
  Image,
  type ImageSourcePropType,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from "react-native";
import type { Market } from "../types/market";
import { formatDistance } from "../utils/formatDistance";
import { Button } from "./Button";
import { DistrictBadge } from "./DistrictBadge";

interface MarketCardProps {
  market: Market;
  onPress: () => void;
  coverImage?: ImageSourcePropType;
}

export function MarketCard({ market, onPress, coverImage }: MarketCardProps) {
  return (
    <TouchableOpacity
      style={styles.card}
      onPress={onPress}
      activeOpacity={0.95}
    >
      {coverImage ? (
        <Image source={coverImage} style={styles.coverImage} />
      ) : (
        <View style={styles.coverPlaceholder}>
          <Ionicons name="cart-outline" size={32} color="#B2DFDB" />
        </View>
      )}

      <View style={styles.content}>
        <View style={styles.topRow}>
          <Text style={styles.marketName} numberOfLines={1}>
            {market.name}
          </Text>
          {market.offersCount != null && market.offersCount > 0 && (
            <View style={styles.offersBadge}>
              <Text style={styles.offersBadgeText}>
                {market.offersCount} OFERTAS
              </Text>
            </View>
          )}
        </View>

        <DistrictBadge neighborhood={market.address} city={market.city} />
      </View>

      <View style={styles.divider} />

      <View style={styles.footer}>
        {market.distanceInKilometers != null ? (
          <View style={styles.distanceRow}>
            <Ionicons name="location-outline" size={16} color="#00838F" />
            <Text style={styles.distanceText}>
              {formatDistance(market.distanceInKilometers)}
            </Text>
          </View>
        ) : (
          <View />
        )}

        <View style={styles.buttonContainer}>
          <Button title="VER OFERTAS" onPress={onPress} />
        </View>
      </View>
    </TouchableOpacity>
  );
}

const styles = StyleSheet.create({
  card: {
    backgroundColor: "#FFFFFF",
    borderRadius: 16,
    borderWidth: 1,
    borderColor: "#E0E0E0",
    overflow: "hidden",
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.08,
    shadowRadius: 8,
    elevation: 3,
    marginHorizontal: 16,
    marginBottom: 16,
  },
  coverImage: {
    width: "100%",
    height: 130,
  },
  coverPlaceholder: {
    width: "100%",
    height: 130,
    backgroundColor: "#E0F7FA",
    alignItems: "center",
    justifyContent: "center",
  },
  content: {
    padding: 16,
    gap: 8,
  },
  topRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    gap: 8,
  },
  marketName: {
    fontSize: 18,
    fontFamily: "Inter-Bold",
    color: "#333333",
    textTransform: "uppercase",
    flexShrink: 1,
  },
  offersBadge: {
    backgroundColor: "#EEEEEE",
    borderRadius: 12,
    paddingHorizontal: 10,
    paddingVertical: 4,
  },
  offersBadgeText: {
    fontSize: 10,
    fontFamily: "Inter-Bold",
    color: "#666666",
    letterSpacing: 0.5,
  },
  divider: {
    borderTopWidth: 1,
    borderColor: "#F5F5F5",
  },
  footer: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    paddingHorizontal: 16,
    paddingVertical: 12,
  },
  distanceRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: 4,
    flexShrink: 1,
  },
  distanceText: {
    fontSize: 14,
    fontFamily: "Inter-SemiBold",
    color: "#00838F",
  },
  buttonContainer: {
    minWidth: 120,
  },
});
