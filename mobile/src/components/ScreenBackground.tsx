import React from "react";
import { StyleSheet, View } from "react-native";

import { colors } from "../theme/tokens";

export default function ScreenBackground() {
  return (
    <View pointerEvents="none" style={StyleSheet.absoluteFill}>
      <View style={styles.topWash} />
      <View style={styles.sideWash} />
    </View>
  );
}

const styles = StyleSheet.create({
  topWash: {
    position: "absolute",
    top: 0,
    left: 0,
    right: 0,
    height: 220,
    backgroundColor: colors.backgroundMuted,
  },
  sideWash: {
    position: "absolute",
    top: 160,
    right: 0,
    width: 140,
    height: 360,
    borderTopLeftRadius: 80,
    borderBottomLeftRadius: 80,
    backgroundColor: "rgba(201, 184, 255, 0.22)",
  },
});
