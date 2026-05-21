import React from "react";
import { StyleProp, StyleSheet, View, ViewStyle } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";

import ScreenBackground from "./ScreenBackground";
import { colors } from "../theme/tokens";

export default function AppScreen({
  children,
  style,
  edges = ["top"],
}: {
  children: React.ReactNode;
  style?: StyleProp<ViewStyle>;
  edges?: Array<"top" | "bottom" | "left" | "right">;
}) {
  return (
    <SafeAreaView style={[styles.container, style]} edges={edges}>
      <ScreenBackground />
      {children}
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.background,
  },
});
