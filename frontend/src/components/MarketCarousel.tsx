import { Ionicons } from "@expo/vector-icons";
import { Dimensions, FlatList, StyleSheet, Text, View } from "react-native";
import type { Market } from "../types/market";
import { formatDistance } from "../utils/formatDistance";
import { Button } from "./Button";
import { DistrictBadge } from "./DistrictBadge";

const { width } = Dimensions.get("window");
const cardWidth = width * 0.45;

export interface CarouselProps {
  markets: Market[];
  handleMarketPress: (market: Market) => void;
}

export const MarketCarousel = (props: CarouselProps) => {
  const renderItem = ({ item }: { item: Market }) => (
    <View style={styles.card}>
      {/* 1. Slot Fixo do Badge de Região/Bairro */}
      <View style={styles.badgeSlot}>
        <DistrictBadge city={item.city} neighborhood={item.address} />
      </View>

      {/* 2. Slot Fixo do Nome do Supermercado (Garante 2 linhas exatas) */}
      <View style={styles.titleSlot}>
        <Text ellipsizeMode="tail" numberOfLines={2} style={styles.name}>
          {item.name}
        </Text>
      </View>

      {/* 3. Slot Fixo da Distância */}
      <View style={styles.distanceSlot}>
        {item.distanceInKilometers != null ? (
          <View style={styles.distanceContainer}>
            <Ionicons color="#1A8A96" name="location-outline" size={13} />
            <Text numberOfLines={1} style={styles.distanceText}>
              {formatDistance(item.distanceInKilometers)} de distância
            </Text>
          </View>
        ) : (
          <View style={styles.distanceContainer} />
        )}
      </View>

      {/* 4. Botão de Ação */}
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
    height: 210,
    borderRadius: 16,
    borderWidth: 1,
    borderColor: "#E0E0E0",
    boxShadow: "0 2px 4px rgba(99, 12, 12, 0.1)",
    justifyContent: "space-between",
    paddingVertical: 14,
    paddingHorizontal: 12,
  },
  badgeSlot: {
    height: 34,
    justifyContent: "center",
  },
  titleSlot: {
    height: 38,
    justifyContent: "center",
  },
  name: {
    fontSize: 14,
    lineHeight: 18,
    fontFamily: "Inter-Bold",
    color: "#333333",
    textAlign: "left",
  },
  distanceSlot: {
    height: 20,
    justifyContent: "center",
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
