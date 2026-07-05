import { Image, StyleSheet, Text, View } from "react-native";
import { findFlag, getDisplayText } from "../utils/raFlags";

interface DistrictBadgeProps {
  neighborhood?: string;
  city?: string;
}

export function DistrictBadge({ neighborhood, city }: DistrictBadgeProps) {
  const displayText = getDisplayText(neighborhood, city);
  if (!displayText) return null;

  const flag = findFlag(neighborhood, city);

  return (
    <View style={styles.badgeContainer}>
      {flag && (
        <Image source={flag} style={styles.flagIcon} resizeMode="contain" />
      )}
      <Text style={styles.badgeText}>{displayText}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  badgeContainer: {
    flexDirection: "row",
    alignItems: "center",
  },
  flagIcon: {
    width: 16,
    height: 12,
    marginRight: 4,
  },
  badgeText: {
    fontSize: 12,
    fontFamily: "Inter-Regular",
    color: "#666666",
  },
});
