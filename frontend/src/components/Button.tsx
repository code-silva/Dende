import type { ReactNode } from "react";
import {
  StyleSheet,
  Text,
  TouchableOpacity,
  type TouchableOpacityProps,
  View,
} from "react-native";

interface ButtonProps extends TouchableOpacityProps {
  title: string;
  onPress: () => void;
  variant?: "primary" | "secondary" | "outline";
  icon?: ReactNode;
}

export function Button({
  title,
  onPress,
  variant = "primary",
  icon,
  ...rest
}: ButtonProps) {
  return (
    <TouchableOpacity
      style={[
        styles.base,
        variant === "primary" && styles.primary,
        variant === "secondary" && styles.secondary,
        variant === "outline" && styles.outline,
      ]}
      onPress={onPress}
      activeOpacity={0.8}
      {...rest}
    >
      {icon && <View style={styles.iconWrapper}>{icon}</View>}
      <Text
        numberOfLines={1}
        style={[
          styles.text,
          variant === "primary" && styles.textPrimary,
          variant === "secondary" && styles.textSecondary,
          variant === "outline" && styles.textOutline,
        ]}
      >
        {title.toUpperCase()}
      </Text>
    </TouchableOpacity>
  );
}

const styles = StyleSheet.create({
  base: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    paddingVertical: 6,
    paddingHorizontal: 16,
    borderRadius: 8,
  },
  primary: {
    backgroundColor: "#00838F",
  },
  secondary: {
    backgroundColor: "#E0F7FA",
  },
  outline: {
    backgroundColor: "transparent",
    borderWidth: 1.5,
    borderColor: "#00838F",
  },
  iconWrapper: {
    marginRight: 8,
  },
  text: {
    fontSize: 11,
    fontFamily: "Inter-Bold",
    letterSpacing: 0.5,
  },
  textPrimary: {
    color: "#FFFFFF",
  },
  textSecondary: {
    color: "#00838F",
  },
  textOutline: {
    color: "#00838F",
  },
});
