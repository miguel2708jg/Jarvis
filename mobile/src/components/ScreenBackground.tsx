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
    height: 260,
    backgroundColor: colors.backgroundMuted,
  },
  sideWash: {
    position: "absolute",
    top: 130,
    right: 0,
    width: 118,
    height: 420,
    borderTopLeftRadius: 80,
    borderBottomLeftRadius: 80,
    backgroundColor: "rgba(79, 155, 136, 0.12)",
  },
});
