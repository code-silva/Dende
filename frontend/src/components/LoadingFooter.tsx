import { memo } from "react";
import { ActivityIndicator, StyleSheet, Text, View } from "react-native";

interface LoadingFooterProps {
  isLoading: boolean;
  message?: string;
}

export const LoadingFooter = memo(function LoadingFooter({
  isLoading,
  message = "Carregando mais ofertas...",
}: LoadingFooterProps) {
  if (!isLoading) return null;

  return (
    <View style={styles.container}>
      <ActivityIndicator size="small" color="#28a8b5" />
      <Text style={styles.text}>{message}</Text>
    </View>
  );
});

const styles = StyleSheet.create({
  container: {
    paddingVertical: 15,
    alignItems: "center",
    width: "100%",
  },
  text: {
    marginTop: 5,
    color: "#28a8b5",
    fontSize: 14,
    fontFamily: "Inter-Medium",
  },
});
