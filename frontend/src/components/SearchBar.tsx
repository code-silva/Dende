import { Feather } from "@expo/vector-icons";
import { useEffect, useState } from "react";
import {
  ActivityIndicator,
  Dimensions,
  Keyboard,
  Platform,
  StyleSheet,
  Text,
  TextInput,
  TouchableOpacity,
  View,
} from "react-native";
import { fetchHybridSearch } from "../api/search";
import { colors } from "../theme/colors";
import type { Product } from "../types/product";

const { width: screenWidth } = Dimensions.get("window");

const isUltraNarrow = screenWidth < 330;
const isSmall = screenWidth < 350;

interface SearchBarProps {
  initialValue?: string;
  placeholder?: string;
  onChangeText?: (text: string) => void;
  disableApiSearch?: boolean;
}

export const SearchBar = ({
  initialValue = "",
  placeholder = "Busque por produtos...",
  onChangeText,
  disableApiSearch = false,
}: SearchBarProps) => {
  const [term, setTerm] = useState(initialValue);
  const [isLoading, setIsLoading] = useState(false);
  const [suggestions, setSuggestions] = useState<string[]>([]);
  const [isSearchPerformed, setIsSearchPerformed] = useState(false);
  const [isFocused, setIsFocused] = useState(false);

  const handleSearchAction = (searchTerm: string) => {
    Keyboard.dismiss();
    setIsFocused(false);
    if (!disableApiSearch) fetchHybridSearch(searchTerm);
  };

  useEffect(() => {
    setTerm(initialValue);
  }, [initialValue]);

  useEffect(() => {
    onChangeText?.(term);
  }, [term, onChangeText]);

  useEffect(() => {
    if (disableApiSearch) return;

    if (term.length < 2) {
      setIsLoading(false);
      setSuggestions([]);
      setIsSearchPerformed(false);
      return;
    }

    setIsLoading(true);

    const searchDelay = setTimeout(async () => {
      try {
        const data = await fetchHybridSearch(term);

        if (data.offers) {
          const productNames = data.offers.map(
            (item: Product) => item.productName,
          );
          const uniqueNames = Array.from(new Set(productNames));
          setSuggestions(uniqueNames as string[]);
        }
        setIsSearchPerformed(true);
      } catch (error) {
        console.error("Error in hybrid search:", error);
        setSuggestions([]);
      } finally {
        setIsLoading(false);
      }
    }, 500);

    return () => clearTimeout(searchDelay);
  }, [term, disableApiSearch]);

  return (
    <View style={styles.container}>
      <View style={styles.searchContainer}>
        <TextInput
          style={[
            // @ts-expect-error
            styles.input,
            { fontSize: isUltraNarrow ? 13 : isSmall ? 14 : 16 },
          ]}
          placeholder={placeholder}
          placeholderTextColor="#A0AAB2"
          value={term}
          onChangeText={setTerm}
          autoCapitalize="none"
          underlineColorAndroid="transparent"
          returnKeyType="search"
          onSubmitEditing={() => handleSearchAction(term)}
          onFocus={() => setIsFocused(true)}
          onBlur={() => setIsFocused(false)}
        />

        <View style={styles.iconContainer}>
          <View style={styles.shapeLight} />
          <View style={styles.shapeDark} />

          {/* Lupe Icon*/}
          <View style={styles.iconWrapper}>
            {isLoading && !disableApiSearch ? (
              <ActivityIndicator
                size="small"
                color="#FFFFFF"
                style={isUltraNarrow ? { transform: [{ scale: 0.8 }] } : null}
              />
            ) : (
              <TouchableOpacity
                onPress={() => {
                  handleSearchAction(term);
                }}
              >
                <Feather
                  name="search"
                  size={isUltraNarrow ? 18 : isSmall ? 20 : 24}
                  color="#FFFFFF"
                />
              </TouchableOpacity>
            )}
          </View>
        </View>
      </View>

      {!disableApiSearch &&
        isFocused &&
        term.length >= 2 &&
        suggestions.length > 0 && (
          <View style={styles.suggestionsContainer}>
            {suggestions.map((item) => (
              <TouchableOpacity
                key={item}
                style={styles.suggestionItem}
                onPress={() => {
                  setTerm(item);
                  setSuggestions([]);
                }}
              >
                <Feather
                  name="search"
                  size={16}
                  color="#A0AAB2"
                  style={{ marginRight: 10 }}
                />
                <Text style={styles.suggestionText} numberOfLines={1}>
                  {item}
                </Text>
              </TouchableOpacity>
            ))}
          </View>
        )}

      {!disableApiSearch &&
        isFocused &&
        term.length >= 2 &&
        isSearchPerformed &&
        suggestions.length === 0 &&
        !isLoading && (
          <View style={styles.suggestionsContainer}>
            <View style={styles.emptyItem}>
              <Feather
                name="help-circle"
                size={20}
                color={colors.textPrimary}
                style={{ marginBottom: 8 }}
              />
              <Text style={styles.emptyTitle}>Nenhum resultado encontrado</Text>
              <Text style={styles.emptySubtitle}>
                Tente verificar a ortografia ou use termos mais simples.
              </Text>
            </View>
          </View>
        )}
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    paddingVertical: 12,
    zIndex: 1000,
  },
  searchContainer: {
    flexDirection: "row",
    height: 50,
    borderRadius: 25,
    overflow: "hidden",
    borderWidth: 1,
    borderColor: "#E0E4E8",
    elevation: 3,
    backgroundColor: "#FFF",
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
  },
  input: {
    flex: 1,
    paddingLeft: 20,
    paddingRight: isUltraNarrow ? 20 : 35,
    color: colors.textPrimary,
    ...Platform.select({
      web: {
        outlineStyle: "none",
      },
    }),
  },
  iconContainer: {
    width: isUltraNarrow ? 55 : isSmall ? "20%" : 85,
    position: "relative",
    justifyContent: "center",
    alignItems: "center",
  },
  shapeLight: {
    position: "absolute",
    left: -15,
    width: 60,
    height: 100,
    backgroundColor: "#82D2D5",
    transform: [{ rotate: "30deg" }],
  },
  shapeDark: {
    position: "absolute",
    right: -20,
    width: 80,
    height: 100,
    backgroundColor: "#1EAEB5",
    transform: [{ rotate: "-15deg" }],
  },
  iconWrapper: {
    position: "absolute",
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    justifyContent: "center",
    alignItems: "center",
    zIndex: 10,
  },
  suggestionsContainer: {
    position: "absolute",
    top: 65,
    left: 0,
    right: 0,
    backgroundColor: "#FFF",
    borderRadius: 15,
    elevation: 5,
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.1,
    shadowRadius: 10,
    borderWidth: 1,
    borderColor: "#E0E4E8",
    zIndex: 2000,
    overflow: "hidden",
  },
  suggestionItem: {
    flexDirection: "row",
    alignItems: "center",
    paddingVertical: 14,
    paddingHorizontal: 20,
    borderBottomWidth: 1,
    borderBottomColor: "#F0F2F5",
  },
  suggestionText: {
    fontSize: 15,
    color: "#333",
    fontFamily: "Inter-Regular",
  },
  emptyItem: {
    padding: 20,
    alignItems: "center",
    justifyContent: "center",
  },
  emptyTitle: {
    fontSize: 16,
    fontWeight: "bold",
    color: "#333",
    marginBottom: 4,
  },
  emptySubtitle: {
    fontSize: 13,
    color: "#A0AAB2",
    textAlign: "center",
    lineHeight: 18,
  },
});
