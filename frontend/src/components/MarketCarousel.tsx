import { Ionicons } from "@expo/vector-icons";
import { Dimensions, FlatList, StyleSheet, Text, View } from "react-native";
import type { Market } from "../types/market";
import { formatDistance } from "../utils/formatDistance";
import { Button } from "./Button";
import { DistrictBadge } from "./DistrictBadge";

const { width, height } = Dimensions.get("window");
const cardWidth = width * 0.45;

// INTERFACES
export interface CarouselProps {
  markets: Market[];
  handleMarketPress: (market: Market) => void;
}

export const MarketCarousel = (props: CarouselProps) => {
  const renderItem = ({ item }: { item: Market }) => (
    <View style={styles.card}>
      <DistrictBadge neighborhood={item.address} city={item.city} />

      <Text style={styles.name}>{item.name}</Text>

      {item.distanceInKilometers != null && (
        <View style={styles.distanceContainer}>
          <Ionicons name="location-outline" size={13} color="#1A8A96" />
          <Text style={styles.distanceText}>
            {formatDistance(item.distanceInKilometers)} de distância
          </Text>
        </View>
      )}

      <Button
        title="VER OFERTAS"
        onPress={() => props.handleMarketPress(item)}
      />
    </View>
  );

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Mercados Próximos</Text>
      <FlatList
        data={props.markets}
        keyExtractor={(item) => item.id.toString()}
        renderItem={renderItem}
        horizontal
        ItemSeparatorComponent={() => <View style={{ width: 16 }} />}
        showsHorizontalScrollIndicator={false}
        contentContainerStyle={{
          paddingVertical: 8,
        }}
      />
    </View>
  );
};

// STYLES
const styles = StyleSheet.create({
  container: {
    paddingVertical: 10,
    minHeight: 150,
  },
  title: {
    fontSize: 22,
    fontFamily: "Inter-Bold",
    color: "#333333",
    marginBottom: 8,
  },
  card: {
    backgroundColor: "#FFFFFF",
    width: cardWidth,
    height: height * 0.21,
    borderRadius: 16,
    borderWidth: 1,
    borderColor: "#E0E0E0",
    boxShadow: "0 2px 4px rgba(99, 12, 12, 0.1)",
    justifyContent: "space-between",
    gap: 16,
    padding: 16,
  },
  name: {
    fontSize: 15,
    fontFamily: "Inter-Bold",
    color: "#333333",
    textAlign: "left",
  },
  distanceContainer: {
    flexDirection: "row",
    alignItems: "center",
  },
  distanceText: {
    fontSize: 11,
    fontFamily: "Inter-Medium",
    color: "#1A8A96",
    marginLeft: 4,
  },
});
