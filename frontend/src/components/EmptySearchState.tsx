import { MaterialCommunityIcons } from "@expo/vector-icons";
import { memo } from "react";
import { StyleSheet, Text, View } from "react-native";

interface EmptySearchStateProps {
  query?: string;
}

export const EmptySearchState = memo(function EmptySearchState({
  query,
}: EmptySearchStateProps) {
  return (
    <View style={styles.container}>
      <View style={styles.iconCircle}>
        <MaterialCommunityIcons
          name="help-circle-outline"
          size={40}
          color="#A0AAB2"
        />
      </View>
      <Text style={styles.title}>
        {query
          ? `Nenhum resultado para "${query}"`
          : "Nenhum produto encontrado"}
      </Text>
      <Text style={styles.subtitle}>
        Verifique a ortografia do termo pesquisado ou tente buscar por um
        produto similar.
      </Text>
    </View>
  );
});

const styles = StyleSheet.create({
  container: {
    justifyContent: "center",
    alignItems: "center",
    padding: 24,
    marginTop: 24,
  },
  iconCircle: {
    width: 72,
    height: 72,
    borderRadius: 36,
    backgroundColor: "#EFF3F6",
    alignItems: "center",
    justifyContent: "center",
    marginBottom: 16,
  },
  title: {
    fontSize: 18,
    fontFamily: "Inter-Bold",
    color: "#333333",
    marginBottom: 6,
    textAlign: "center",
  },
  subtitle: {
    fontSize: 14,
    fontFamily: "Inter-Regular",
    color: "#888888",
    textAlign: "center",
    lineHeight: 20,
  },
});
