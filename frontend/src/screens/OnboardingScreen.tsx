import React, { useRef, useState, useCallback } from "react";
import { View, SafeAreaView, FlatList, Dimensions, StyleSheet } from "react-native";
import type { ViewToken } from "react-native";
import WelcomeSlide from "../components/onboarding/WelcomeSlide";
import HowItWorksSlide from "../components/onboarding/HowItWorksSlide";
import DetailsSlide from "../components/onboarding/DetailsSlide";
import ConsentSlide from "../components/onboarding/Consent";
import { useAuth } from "../contexts/AuthContext";

const { width: SCREEN_WIDTH } = Dimensions.get("window");

interface SlideItem {
  key: string;
}

const slides: SlideItem[] = [
  { key: "welcome" },
  { key: "how-it-works" },
  { key: "details" },
  { key: "consent" },
];

export default function OnboardingScreen() {
  const [currentSlide, setCurrentSlide] = useState(0);
  const flatListRef = useRef<FlatList<SlideItem>>(null);
  const { setHasCompletedOnboarding } = useAuth();

  const goToSlide = (index: number) => {
    if (index < 0 || index >= slides.length) return;
    flatListRef.current?.scrollToIndex({ index, animated: true });
    setCurrentSlide(index);
  };

  const goToNextSlide = async () => {
    if (currentSlide < slides.length - 1) {
      goToSlide(currentSlide + 1);
    } else {
      setHasCompletedOnboarding(true);
    }
  };

  const goToPreviousSlide = () => goToSlide(currentSlide - 1);

  const onViewableItemsChanged = useRef(
    ({ viewableItems }: { viewableItems: Array<ViewToken> }) => {
      if (viewableItems.length > 0) {
        const idx = viewableItems[0].index ?? 0;
        setCurrentSlide(idx);
      }
    }
  ).current;

  const viewabilityConfig = useRef({
    itemVisiblePercentThreshold: 50,
  }).current;

  const renderItem = useCallback(
    ({ index }: { index: number }) => {
      const commonProps = { currentSlide, goToNextSlide, goToPreviousSlide };

      switch (index) {
        case 0:
          return (
            <View style={[styles.slide, { width: SCREEN_WIDTH }]}>
              <WelcomeSlide {...commonProps} />
            </View>
          );
        case 1:
          return (
            <View style={[styles.slide, { width: SCREEN_WIDTH }]}>
              <HowItWorksSlide {...commonProps} />
            </View>
          );
        case 2:
          return (
            <View style={[styles.slide, { width: SCREEN_WIDTH }]}>
              <DetailsSlide {...commonProps} />
            </View>
          );
        case 3:
          return (
            <View style={[styles.slide, { width: SCREEN_WIDTH }]}>
              <ConsentSlide {...commonProps} />
            </View>
          );
        default:
          return null;
      }
    },
    [currentSlide]
  );

  return (
    <SafeAreaView style={styles.container}>
      <FlatList
        ref={flatListRef}
        data={slides}
        keyExtractor={(item) => item.key}
        horizontal
        pagingEnabled
        showsHorizontalScrollIndicator={false}
        renderItem={renderItem}
        onViewableItemsChanged={onViewableItemsChanged}
        viewabilityConfig={viewabilityConfig}
        getItemLayout={(_, index) => ({
          length: SCREEN_WIDTH,
          offset: SCREEN_WIDTH * index,
          index,
        })}
        initialNumToRender={1}
        windowSize={2}
      />

      <View style={styles.progressContainer}>
        {slides.map((_, idx) => (
          <View
            key={idx}
            style={[styles.dot, idx === currentSlide && styles.dotActive]}
          />
        ))}
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: "#fff" },
  slide: { flex: 1 },
  progressContainer: {
    position: "absolute",
    bottom: 28,
    left: 0,
    right: 0,
    flexDirection: "row",
    justifyContent: "center",
    gap: 8,
  },
  dot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    backgroundColor: "#e0e0e0",
    marginHorizontal: 4,
  },
  dotActive: {
    width: 22,
    backgroundColor: "#9ACDAF",
  },
});
