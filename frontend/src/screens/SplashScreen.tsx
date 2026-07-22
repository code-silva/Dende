import { LinearGradient } from "expo-linear-gradient";
import React, { useEffect, useRef, useState } from "react";
import {
  Animated,
  Dimensions,
  Easing,
  Image,
  StyleSheet,
  Text,
  View,
} from "react-native";

const { width: screenWidth } = Dimensions.get("window");

const LOADING_ITEMS = [
  {
    image: require("../assets/splash/stickman.png"),
    label: "Buscando preços...",
  },
  {
    image: require("../assets/splash/apple.png"),
    label: "Atualizando hortifrúti...",
  },
  {
    image: require("../assets/splash/rice.png"),
    label: "Verificando despensa...",
  },
  {
    image: require("../assets/splash/meat.png"),
    label: "Avaliando ofertas...",
  },
];

interface SplashScreenProps {
  onAnimationEnd: () => void;
}

export default function SplashScreen({ onAnimationEnd }: SplashScreenProps) {
  const [phase, setPhase] = useState<"brand" | "loading">("brand");
  const [loadingIndex, setLoadingIndex] = useState(0);

  const brandOpacity = useRef(new Animated.Value(0)).current;
  const brandScale = useRef(new Animated.Value(0.8)).current;
  const brandFade = useRef(new Animated.Value(1)).current;
  const loadingOpacity = useRef(new Animated.Value(0)).current;
  const progressScaleX = useRef(new Animated.Value(0)).current;
  const iconFade = useRef(new Animated.Value(1)).current;

  useEffect(() => {
    Animated.parallel([
      Animated.timing(brandOpacity, {
        toValue: 1,
        duration: 600,
        easing: Easing.out(Easing.quad),
        useNativeDriver: true,
      }),
      Animated.timing(brandScale, {
        toValue: 1,
        duration: 600,
        easing: Easing.out(Easing.quad),
        useNativeDriver: true,
      }),
    ]).start(() => {
      setTimeout(() => {
        setPhase("loading");
      }, 2000);
    });
  }, []);

  useEffect(() => {
    if (phase !== "loading") return;

    Animated.parallel([
      Animated.timing(brandFade, {
        toValue: 0,
        duration: 400,
        useNativeDriver: true,
      }),
      Animated.timing(loadingOpacity, {
        toValue: 1,
        duration: 400,
        useNativeDriver: true,
      }),
    ]).start();

    Animated.timing(progressScaleX, {
      toValue: 1,
      duration: 2500,
      useNativeDriver: true,
    }).start(() => {
      onAnimationEnd();
    });
  }, [phase]);

  useEffect(() => {
    if (phase !== "loading") return;
    if (loadingIndex >= LOADING_ITEMS.length - 1) return;

    const timer = setTimeout(() => {
      iconFade.setValue(0);
      Animated.timing(iconFade, {
        toValue: 1,
        duration: 300,
        useNativeDriver: true,
      }).start();
      setLoadingIndex((prev) => prev + 1);
    }, 600);

    return () => clearTimeout(timer);
  }, [loadingIndex, phase]);

  const currentItem = LOADING_ITEMS[loadingIndex];

  return (
    <View style={styles.container}>
      <LinearGradient colors={["#2BCBDC", "#176D76"]} style={styles.background}>
        {/* Phase 1: Brand presentation */}
        {phase === "brand" && (
          <Animated.View
            style={[
              styles.brandWrapper,
              {
                opacity: brandOpacity,
                transform: [{ scale: brandScale }],
              },
            ]}
          >
            <Image
              source={require("../assets/splash/logo_dende.png")}
              style={styles.logo}
              resizeMode="contain"
            />
            <Text style={styles.title}>Dendê</Text>
          </Animated.View>
        )}

        {/* Phase 1 brand fade-out overlay */}
        {phase === "loading" && (
          <Animated.View
            style={[
              styles.brandWrapper,
              {
                opacity: brandFade,
                transform: [{ scale: brandScale }],
              },
            ]}
            pointerEvents="none"
          >
            <Image
              source={require("../assets/splash/logo_dende.png")}
              style={styles.logo}
              resizeMode="contain"
            />
            <Text style={styles.title}>Dendê</Text>
          </Animated.View>
        )}

        {/* Phase 2: Loading with stickman circle */}
        <Animated.View
          style={[styles.loadingWrapper, { opacity: loadingOpacity }]}
          pointerEvents={phase !== "loading" ? "none" : "auto"}
        >
          <View style={styles.stickmanCircle}>
            <Animated.Image
              source={currentItem.image}
              style={[styles.stickmanImage, { opacity: iconFade }]}
              resizeMode="contain"
            />
          </View>

          <Text style={styles.loadingLabel}>{currentItem.label}</Text>

          <View style={styles.progressTrack}>
            <Animated.View
              style={[
                styles.progressFill,
                { transform: [{ scaleX: progressScaleX }] },
              ]}
            />
          </View>
        </Animated.View>
      </LinearGradient>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  background: {
    flex: 1,
    justifyContent: "center",
    alignItems: "center",
  },
  brandWrapper: {
    position: "absolute",
    alignItems: "center",
    justifyContent: "center",
  },
  logo: {
    width: 80,
    height: 80,
    marginBottom: 8,
  },
  title: {
    fontSize: 22,
    fontWeight: "bold",
    color: "#FFFFFF",
    textAlign: "center",
  },
  loadingWrapper: {
    position: "absolute",
    alignItems: "center",
    justifyContent: "center",
  },
  stickmanCircle: {
    width: 140,
    height: 140,
    borderRadius: 70,
    backgroundColor: "#FFFFFF",
    justifyContent: "center",
    alignItems: "center",
    marginBottom: 24,
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.15,
    shadowRadius: 8,
    elevation: 4,
  },
  stickmanImage: {
    width: 80,
    height: 80,
  },
  loadingLabel: {
    fontSize: 16,
    color: "#FFFFFF",
    fontWeight: "500",
    marginBottom: 24,
  },
  progressTrack: {
    width: screenWidth * 0.7,
    height: 6,
    backgroundColor: "rgba(255, 255, 255, 0.3)",
    borderRadius: 3,
    overflow: "hidden",
  },
  progressFill: {
    height: "100%",
    backgroundColor: "#FFFFFF",
    borderRadius: 3,
    transformOrigin: "left",
  },
});
