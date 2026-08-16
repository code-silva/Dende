import { MaterialIcons } from "@expo/vector-icons";
import { StyleSheet, Text, View } from "react-native";
import { colors } from "../theme/colors";

interface AiInfoBannerProps {
  title?: string;
  description?: string;
}

export const AiInfoBanner = ({
  title = "Extração via IA",
  description = "A extração de dados via IA pode apresentar falhas. Viu uma informação diferente no mercado? Use o botão Reportar Oferta e ajude todo mundo a economizar com dados precisos.",
}: AiInfoBannerProps) => {
  return (
    <View style={styles.container}>
      <View style={styles.iconContainer}>
        <MaterialIcons name="smart-toy" size={40} color={colors.infoIcon} />
      </View>

      <View style={styles.textContainer}>
        <Text style={styles.title}>{title}</Text>
        <Text style={styles.description}>{description}</Text>
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flexDirection: "row",
    backgroundColor: colors.infoBackground,
    borderRadius: 8,
    marginVertical: 10,
    padding: 15,
    borderLeftWidth: 4,
    borderLeftColor: colors.infoBorder,
    alignItems: "center",
  },
  iconContainer: {
    marginRight: 15,
  },
  textContainer: {
    flex: 1,
  },
  title: {
    fontSize: 18,
    fontWeight: "bold",
    color: colors.textPrimary,
    marginBottom: 2,
  },
  description: {
    fontSize: 13,
    color: colors.textSecondary,
    lineHeight: 18,
  },
});
