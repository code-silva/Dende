import { Feather } from "@expo/vector-icons";
import { memo } from "react";
import { StyleSheet, Text, View } from "react-native";

export const EmptySearchState = memo(function EmptySearchState() {
  return (
    <View style={styles.container}>
      <View style={styles.iconWrapper}>
        <Feather name="help-circle" size={40} color="#A0AAB2" />
      </View>
      <Text style={styles.title}>Nenhum produto encontrado neste mercado</Text>
      <Text style={styles.subtitle}>
        Tente buscar por outro termo ou verifique a ortografia do que digitou.
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
  iconWrapper: {
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
