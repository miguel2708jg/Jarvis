import React from "react";
import { StyleSheet, Text, TouchableOpacity, View } from "react-native";

import { colors, radii, shadows, spacing } from "../theme/tokens";

type HeroStat = {
  label: string;
  value: string;
};

interface Props {
  eyebrow: string;
  title: string;
  subtitle: string;
  actionLabel?: string;
  onActionPress?: () => void;
  stats?: HeroStat[];
  error?: string | null;
  children?: React.ReactNode;
}

export default function ModuleHero({
  eyebrow,
  title,
  subtitle,
  actionLabel,
  onActionPress,
  stats = [],
  error,
  children,
}: Props) {
  return (
    <View style={styles.shell}>
      <View style={styles.glowPrimary} />
      <View style={styles.glowSecondary} />

      <View style={styles.topRow}>
        <View style={styles.copyBlock}>
          <Text style={styles.eyebrow}>{eyebrow}</Text>
          <Text style={styles.title}>{title}</Text>
          <Text style={styles.subtitle}>{subtitle}</Text>
        </View>

        {actionLabel && onActionPress ? (
          <TouchableOpacity style={styles.actionButton} onPress={onActionPress}>
            <Text style={styles.actionText}>{actionLabel}</Text>
          </TouchableOpacity>
        ) : null}
      </View>

      {stats.length > 0 ? (
        <View style={styles.statsRow}>
          {stats.map((stat) => (
            <View key={stat.label} style={styles.statCard}>
              <Text style={styles.statValue}>{stat.value}</Text>
              <Text style={styles.statLabel}>{stat.label}</Text>
            </View>
          ))}
        </View>
      ) : null}

      {children}

      {error ? <Text style={styles.errorBanner}>{error}</Text> : null}
    </View>
  );
}

const styles = StyleSheet.create({
  shell: {
    position: "relative",
    overflow: "hidden",
    backgroundColor: colors.ink,
    borderRadius: radii.lg,
    padding: spacing.lg,
    marginBottom: spacing.lg,
    ...shadows.card,
  },
  glowPrimary: {
    position: "absolute",
    width: 180,
    height: 180,
    borderRadius: 999,
    top: -90,
    right: -40,
    backgroundColor: "rgba(27, 183, 199, 0.22)",
  },
  glowSecondary: {
    position: "absolute",
    width: 160,
    height: 160,
    borderRadius: 999,
    bottom: -80,
    left: -30,
    backgroundColor: "rgba(212, 145, 52, 0.18)",
  },
  topRow: {
    flexDirection: "row",
    alignItems: "flex-start",
    justifyContent: "space-between",
  },
  copyBlock: {
    flex: 1,
    paddingRight: spacing.md,
  },
  eyebrow: {
    color: "#99ECF5",
    fontSize: 11,
    fontWeight: "800",
    letterSpacing: 1.6,
    textTransform: "uppercase",
    marginBottom: spacing.sm,
  },
  title: {
    color: colors.white,
    fontSize: 27,
    lineHeight: 31,
    fontWeight: "800",
    marginBottom: spacing.sm,
  },
  subtitle: {
    color: "rgba(255, 255, 255, 0.74)",
    fontSize: 14,
    lineHeight: 21,
  },
  actionButton: {
    alignSelf: "flex-start",
    borderRadius: radii.pill,
    backgroundColor: colors.white,
    paddingHorizontal: 14,
    paddingVertical: 10,
  },
  actionText: {
    color: colors.ink,
    fontSize: 13,
    fontWeight: "700",
  },
  statsRow: {
    flexDirection: "row",
    flexWrap: "wrap",
    marginTop: spacing.lg,
  },
  statCard: {
    minWidth: 92,
    flexGrow: 1,
    backgroundColor: "rgba(255, 255, 255, 0.12)",
    borderRadius: radii.md,
    padding: 14,
    marginRight: spacing.sm,
    marginBottom: spacing.sm,
    borderWidth: 1,
    borderColor: "rgba(255, 255, 255, 0.08)",
  },
  statValue: {
    color: colors.white,
    fontSize: 22,
    fontWeight: "800",
    marginBottom: 4,
  },
  statLabel: {
    color: "rgba(255, 255, 255, 0.68)",
    fontSize: 12,
    fontWeight: "600",
  },
  errorBanner: {
    marginTop: spacing.md,
    paddingHorizontal: 12,
    paddingVertical: 10,
    borderRadius: radii.sm,
    backgroundColor: colors.dangerSoft,
    color: colors.danger,
    fontSize: 13,
    fontWeight: "600",
  },
});
