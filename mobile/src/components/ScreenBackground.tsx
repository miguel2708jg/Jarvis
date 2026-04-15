import React from "react";
import { StyleSheet, View } from "react-native";

import { colors } from "../theme/tokens";

export default function ScreenBackground() {
  return (
    <View pointerEvents="none" style={StyleSheet.absoluteFill}>
      <View style={[styles.orb, styles.orbTop]} />
      <View style={[styles.orb, styles.orbRight]} />
      <View style={[styles.orb, styles.orbBottom]} />
      <View style={styles.gridStripe} />
    </View>
  );
}

const styles = StyleSheet.create({
  orb: {
    position: "absolute",
    borderRadius: 999,
  },
  orbTop: {
    width: 260,
    height: 260,
    top: -110,
    left: -70,
    backgroundColor: "rgba(27, 183, 199, 0.12)",
  },
  orbRight: {
    width: 220,
    height: 220,
    top: 80,
    right: -80,
    backgroundColor: "rgba(212, 145, 52, 0.10)",
  },
  orbBottom: {
    width: 300,
    height: 300,
    bottom: -180,
    left: "10%",
    backgroundColor: "rgba(23, 32, 51, 0.05)",
  },
  gridStripe: {
    position: "absolute",
    top: 124,
    left: 24,
    right: 24,
    height: 1,
    backgroundColor: colors.border,
    opacity: 0.45,
  },
});
