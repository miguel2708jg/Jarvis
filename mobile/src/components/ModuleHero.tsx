import React from "react";
import { StyleSheet, Text, TouchableOpacity, View } from "react-native";

import { ErrorBanner, MetricCard } from "./design";
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
      <View style={styles.sunDot} />

      <View style={styles.topRow}>
        <View style={styles.copyBlock}>
          <Text style={styles.eyebrow}>{eyebrow}</Text>
          <Text style={styles.title}>{title}</Text>
          <Text style={styles.subtitle}>{subtitle}</Text>
        </View>

        {actionLabel && onActionPress ? (
          <TouchableOpacity style={styles.actionButton} onPress={onActionPress}>
            <Text style={styles.actionPlus}>+</Text>
            <Text style={styles.actionText}>{actionLabel}</Text>
          </TouchableOpacity>
        ) : null}
      </View>

      {stats.length > 0 ? (
        <View style={styles.statsRow}>
          {stats.map((stat) => <MetricCard key={stat.label} label={stat.label} value={stat.value} />)}
        </View>
      ) : null}

      {children}

      <ErrorBanner error={error} />
    </View>
  );
}

const styles = StyleSheet.create({
  shell: {
    position: "relative",
    overflow: "hidden",
    backgroundColor: colors.primarySoft,
    borderRadius: radii.xl,
    padding: spacing.lg,
    marginBottom: spacing.lg,
    borderWidth: 1,
    borderColor: "rgba(47, 125, 106, 0.16)",
    ...shadows.card,
  },
  accentBlock: {
    position: "absolute",
    width: 126,
    height: 126,
    borderRadius: 28,
    top: -34,
    right: -24,
    backgroundColor: "rgba(255, 255, 255, 0.45)",
    transform: [{ rotate: "12deg" }],
  },
  sunDot: {
    position: "absolute",
    right: 24,
    bottom: 24,
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: colors.warning,
    borderWidth: 6,
    borderColor: "rgba(255, 255, 255, 0.58)",
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
    color: colors.primaryStrong,
    fontSize: 11,
    fontWeight: "800",
    letterSpacing: 1.2,
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
    color: colors.textMuted,
    fontSize: 14,
    lineHeight: 21,
  },
  actionButton: {
    flexDirection: "row",
    alignItems: "center",
    alignSelf: "flex-start",
    borderRadius: radii.pill,
    backgroundColor: colors.warning,
    paddingHorizontal: 13,
    paddingVertical: 10,
  },
  actionPlus: {
    color: colors.ink,
    fontSize: 15,
    fontWeight: "900",
    marginRight: 6,
  },
  actionText: {
    color: colors.ink,
    fontSize: 13,
    fontWeight: "800",
  },
  statsRow: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: spacing.sm,
    marginTop: spacing.lg,
  },
});
