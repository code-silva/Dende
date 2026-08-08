import { Feather } from "@expo/vector-icons";
import { useState } from "react";
import {
  Modal,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from "react-native";
import { colors } from "../theme/colors";

interface CityFilterProps {
  cities: string[];
  selectedCity: string | null;
  onSelectCity: (city: string | null) => void;
  onClearFilters?: () => void;
}

export const CityFilter = ({
  cities,
  selectedCity,
  onSelectCity,
  onClearFilters,
}: CityFilterProps) => {
  const [isOpen, setIsOpen] = useState(false);

  const handleSelect = (city: string | null) => {
    onSelectCity(city);
    setIsOpen(false);
  };

  return (
    <View>
      <TouchableOpacity
        style={styles.trigger}
        onPress={() => setIsOpen(true)}
        activeOpacity={0.8}
        accessibilityRole="button"
        accessibilityLabel="Filtrar por cidade"
        accessibilityHint="Abre a lista de cidades disponíveis"
      >
        <Feather name="map-pin" size={16} color={colors.primary} />
        <Text
          style={[
            styles.triggerText,
            !selectedCity && styles.triggerPlaceholder,
          ]}
          numberOfLines={1}
        >
          {selectedCity ?? "Todas as cidades"}
        </Text>
        <Feather name="chevron-down" size={16} color={colors.textSecondary} />
      </TouchableOpacity>

      <Modal
        visible={isOpen}
        transparent
        animationType="fade"
        onRequestClose={() => setIsOpen(false)}
      >
        <Pressable style={styles.backdrop} onPress={() => setIsOpen(false)}>
          <View style={styles.sheet}>
            <Text style={styles.sheetTitle}>Filtrar por cidade</Text>

            <TouchableOpacity
              style={styles.option}
              onPress={() => {
                if (onClearFilters) {
                  onClearFilters();
                } else {
                  onSelectCity(null);
                }
                setIsOpen(false);
              }}
              activeOpacity={0.7}
            >
              <Feather
                name={selectedCity == null ? "check-circle" : "circle"}
                size={18}
                color={selectedCity == null ? colors.primary : "#C0C4CC"}
              />
              <Text style={styles.optionText}>Limpar Filtros</Text>
            </TouchableOpacity>

            <ScrollView style={styles.optionsList} bounces={false}>
              {cities.map((city) => (
                <TouchableOpacity
                  key={city}
                  style={styles.option}
                  onPress={() => handleSelect(city)}
                  activeOpacity={0.7}
                >
                  <Feather
                    name={selectedCity === city ? "check-circle" : "circle"}
                    size={18}
                    color={selectedCity === city ? colors.primary : "#C0C4CC"}
                  />
                  <Text style={styles.optionText}>{city}</Text>
                </TouchableOpacity>
              ))}
            </ScrollView>
          </View>
        </Pressable>
      </Modal>
    </View>
  );
};

const styles = StyleSheet.create({
  trigger: {
    flexDirection: "row",
    alignItems: "center",
    alignSelf: "flex-start",
    gap: 6,
    paddingVertical: 8,
    paddingHorizontal: 12,
    borderRadius: 20,
    borderWidth: 1,
    borderColor: "#E0E4E8",
    backgroundColor: "#FFF",
    maxWidth: "100%",
  },
  triggerText: {
    fontSize: 14,
    fontFamily: "Inter-Medium",
    color: colors.textPrimary,
    flexShrink: 1,
  },
  triggerPlaceholder: {
    color: colors.textSecondary,
  },
  backdrop: {
    flex: 1,
    justifyContent: "flex-end",
    backgroundColor: "rgba(0, 0, 0, 0.4)",
  },
  sheet: {
    backgroundColor: "#FFF",
    borderTopLeftRadius: 20,
    borderTopRightRadius: 20,
    paddingTop: 20,
    paddingBottom: 32,
    paddingHorizontal: 16,
    maxHeight: "70%",
  },
  sheetTitle: {
    fontSize: 16,
    fontFamily: "Inter-Bold",
    color: colors.textPrimary,
    marginBottom: 12,
  },
  optionsList: {
    marginTop: 4,
  },
  option: {
    flexDirection: "row",
    alignItems: "center",
    gap: 10,
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: "#F0F2F5",
  },
  optionText: {
    fontSize: 15,
    fontFamily: "Inter-Regular",
    color: colors.textPrimary,
  },
});
