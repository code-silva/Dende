import { StyleSheet, Text, View } from "react-native";
import { DistrictBadge } from "./DistrictBadge";

interface MarketBannerProps {
  marketName: string;
  subtitle: string;
  address?: string;
}

export function MarketBanner({
  marketName,
  subtitle,
  address,
}: MarketBannerProps) {
  const firstLetter = marketName ? marketName[0].toUpperCase() : "?";
  const displayName = marketName ? marketName.toUpperCase() : "LOADING...";

  return (
    <View style={styles.marketBanner}>
      <View style={styles.marketLogo}>
        <Text style={styles.marketInitials}>{firstLetter}</Text>
      </View>

      <View style={styles.textContainer}>
        {!!address && (
          <View style={{ marginBottom: 4 }}>
            <DistrictBadge neighborhood={address} />
          </View>
        )}

        <Text style={styles.marketName}>{displayName}</Text>
        <Text style={styles.marketStatus}>{subtitle}</Text>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  marketBanner: {
    flexDirection: "row",
    alignItems: "flex-start",
    padding: 15,
    backgroundColor: "#FFF",
    marginHorizontal: 10,
    borderRadius: 12,
    marginBottom: 10,
    borderWidth: 1,
    borderColor: "#EEE",
  },
  textContainer: {
    flex: 1,
    flexDirection: "column",
    alignItems: "flex-start",
    justifyContent: "flex-start",
  },
  marketInitials: {
    fontSize: 20,
    fontFamily: "Inter-Bold",
    color: "#28a8b5",
  },
  marketLogo: {
    width: 80,
    height: 50,
    borderRadius: 30,
    backgroundColor: "#f8f8f8",
    justifyContent: "center",
    alignItems: "center",
    marginRight: 12,
    borderWidth: 1,
    borderColor: "#DDD",
  },
  marketName: {
    fontFamily: "Inter-Bold",
    fontSize: 16,
    color: "#000",
    marginTop: 6,
  },
  marketStatus: {
    fontSize: 10,
    color: "#28a8b5",
    fontFamily: "Inter-Bold",
  },
});
