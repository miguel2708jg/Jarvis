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
      <View style={styles.accentBlock} />

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
    backgroundColor: colors.lavender,
    borderRadius: radii.lg,
    padding: spacing.lg,
    marginBottom: spacing.lg,
    ...shadows.card,
  },
  accentBlock: {
    position: "absolute",
    width: 116,
    height: 116,
    borderRadius: 36,
    top: -28,
    right: -18,
    backgroundColor: "rgba(255, 255, 255, 0.34)",
    transform: [{ rotate: "12deg" }],
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
    color: colors.ink,
    fontSize: 11,
    fontWeight: "800",
    letterSpacing: 1.6,
    textTransform: "uppercase",
    marginBottom: spacing.sm,
  },
  title: {
    color: colors.ink,
    fontSize: 27,
    lineHeight: 31,
    fontWeight: "800",
    marginBottom: spacing.sm,
  },
  subtitle: {
    color: "rgba(9, 10, 20, 0.68)",
    fontSize: 14,
    lineHeight: 21,
  },
  actionButton: {
    alignSelf: "flex-start",
    borderRadius: radii.pill,
    backgroundColor: colors.ink,
    paddingHorizontal: 14,
    paddingVertical: 10,
  },
  actionText: {
    color: colors.white,
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
    backgroundColor: "rgba(255, 255, 255, 0.58)",
    borderRadius: radii.md,
    padding: 14,
    marginRight: spacing.sm,
    marginBottom: spacing.sm,
    borderWidth: 1,
    borderColor: "rgba(255, 255, 255, 0.46)",
  },
  statValue: {
    color: colors.ink,
    fontSize: 22,
    fontWeight: "800",
    marginBottom: 4,
  },
  statLabel: {
    color: colors.textMuted,
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
