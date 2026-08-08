import React from "react";
import { StyleSheet, Text, View } from "react-native";
import type { Market } from "../types/market";
import { InfoBanner } from "./InfoBanner";
import { MarketCarousel } from "./MarketCarousel";
import { SearchBar } from "./SearchBar";

// INTEFACE
interface HomeHeaderProps {
  markets: Market[];
  handleMarketPress: (market: Market) => void;
  onSearch: (term: string) => void;
}

// COMPONENT
export const HomeHeader = React.memo((props: HomeHeaderProps) => (
  <View style={styles.headerContainer}>
    <SearchBar onSearch={props.onSearch} />

    {props.markets.length > 0 && (
      <MarketCarousel
        markets={props.markets}
        handleMarketPress={props.handleMarketPress}
      />
    )}

    <InfoBanner />
    <Text style={styles.sectionTitle}>Ofertas do Dia</Text>
  </View>
));

// Styles
export const styles = StyleSheet.create({
  headerContainer: {
    width: "100%",
    paddingBottom: 10,
    alignSelf: "stretch",
    zIndex: 10,
    overflow: "visible",
  },
  sectionTitle: {
    fontSize: 22,
    fontFamily: "Inter-Bold",
    color: "#333333",
    marginTop: 10,
  },
});
