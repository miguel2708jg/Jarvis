import React, { useCallback } from "react";
import {
  ActivityIndicator,
  Alert,
  FlatList,
  RefreshControl,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { useFocusEffect } from "@react-navigation/native";
import { Ionicons } from "@expo/vector-icons";

import ModuleHero from "../components/ModuleHero";
import ScreenBackground from "../components/ScreenBackground";
import { useCalendar } from "../hooks/useJarvisApi";
import { colors, radii, shadows, spacing } from "../theme/tokens";

function formatDate(iso: string): string {
  const date = new Date(iso);
  return date.toLocaleString(undefined, {
    weekday: "short",
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function formatDayLabel(iso: string): string {
  const date = new Date(iso);
  return date.toLocaleDateString(undefined, {
    month: "short",
    day: "numeric",
  });
}

export default function CalendarScreen() {
  const { items: events, loading, error, refresh, remove } = useCalendar();
  const nextEvent = events[0];

  useFocusEffect(
    useCallback(() => {
      refresh();
    }, [refresh])
  );

  if (loading && events.length === 0) {
    return (
      <View style={styles.center}>
        <ActivityIndicator size="large" color={colors.accentStrong} />
      </View>
    );
  }

  return (
    <SafeAreaView style={styles.container} edges={["top"]}>
      <ScreenBackground />

      <FlatList
        data={events}
        keyExtractor={(event) => event.id}
        contentContainerStyle={styles.list}
        refreshControl={
          <RefreshControl refreshing={loading} onRefresh={() => refresh()} tintColor={colors.accentStrong} />
        }
        ListHeaderComponent={
          <ModuleHero
            eyebrow="Calendar"
            title="Upcoming time blocks with enough hierarchy to scan fast."
            subtitle="Use chat to schedule events, then manage the resulting agenda here without losing the broader timeline."
            stats={[
              { label: "Upcoming", value: String(events.length) },
              {
                label: "Next event",
                value: nextEvent ? formatDayLabel(nextEvent.start_datetime) : "None set",
              },
            ]}
            error={error}
          >
            <View style={styles.heroHintRow}>
              <View style={styles.heroHintChip}>
                <Ionicons name="sparkles-outline" size={14} color={colors.accentStrong} />
                <Text style={styles.heroHintText}>Ask Jarvis to schedule from chat</Text>
              </View>
            </View>
          </ModuleHero>
        }
        ListEmptyComponent={
          <View style={styles.emptyCard}>
            <Text style={styles.emptyTitle}>No events yet.</Text>
            <Text style={styles.emptyText}>
              Ask Jarvis to schedule a meeting, add a deadline, or build an agenda for the week.
            </Text>
          </View>
        }
        renderItem={({ item }) => (
          <TouchableOpacity
            style={styles.card}
            onLongPress={() =>
              Alert.alert("Delete event", `Delete "${item.title}"?`, [
                { text: "Cancel", style: "cancel" },
                { text: "Delete", style: "destructive", onPress: () => remove(item.id) },
              ])
            }
          >
            <View style={styles.datePill}>
              <Text style={styles.datePillDay}>{formatDayLabel(item.start_datetime)}</Text>
              <Text style={styles.datePillTime}>
                {new Date(item.start_datetime).toLocaleTimeString(undefined, {
                  hour: "2-digit",
                  minute: "2-digit",
                })}
              </Text>
            </View>

            <View style={styles.info}>
              <Text style={styles.title}>{item.title}</Text>
              <View style={styles.metaRow}>
                <Ionicons name="time-outline" size={14} color={colors.textSoft} />
                <Text style={styles.metaText}>{formatDate(item.start_datetime)}</Text>
              </View>

              {item.location ? (
                <View style={styles.metaRow}>
                  <Ionicons name="location-outline" size={14} color={colors.textSoft} />
                  <Text style={styles.metaText}>{item.location}</Text>
                </View>
              ) : null}

              {item.description ? (
                <Text style={styles.description} numberOfLines={3}>
                  {item.description}
                </Text>
              ) : null}
            </View>
          </TouchableOpacity>
        )}
      />
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.background,
  },
  center: {
    flex: 1,
    alignItems: "center",
    justifyContent: "center",
    backgroundColor: colors.background,
  },
  list: {
    padding: spacing.md,
    paddingBottom: 128,
  },
  heroHintRow: {
    flexDirection: "row",
    flexWrap: "wrap",
    marginTop: spacing.md,
  },
  heroHintChip: {
    flexDirection: "row",
    alignItems: "center",
    borderRadius: radii.pill,
    borderWidth: 1,
    borderColor: colors.borderSecondary,
    backgroundColor: colors.surfaceMuted,
    paddingHorizontal: 12,
    paddingVertical: 9,
  },
  heroHintText: {
    color: colors.ink,
    fontSize: 12,
    fontWeight: "700",
    marginLeft: 8,
  },
  emptyCard: {
    backgroundColor: colors.surface,
    borderRadius: radii.lg,
    padding: spacing.xl,
    borderWidth: 1,
    borderColor: colors.border,
    ...shadows.soft,
  },
  emptyTitle: {
    color: colors.text,
    fontSize: 24,
    fontWeight: "800",
    marginBottom: spacing.sm,
  },
  emptyText: {
    color: colors.textMuted,
    fontSize: 15,
    lineHeight: 23,
  },
  card: {
    flexDirection: "row",
    backgroundColor: colors.surface,
    borderRadius: radii.lg,
    padding: spacing.md,
    marginBottom: 14,
    borderWidth: 1,
    borderColor: colors.border,
    ...shadows.soft,
  },
  datePill: {
    width: 86,
    borderRadius: radii.md,
    backgroundColor: colors.skySoft,
    borderWidth: 1,
    borderColor: colors.borderSecondary,
    alignItems: "center",
    justifyContent: "center",
    paddingVertical: 16,
    paddingHorizontal: 10,
    marginRight: spacing.md,
  },
  datePillDay: {
    color: colors.ink,
    fontSize: 15,
    fontWeight: "800",
    marginBottom: 4,
  },
  datePillTime: {
    color: colors.textMuted,
    fontSize: 12,
    fontWeight: "700",
  },
  info: {
    flex: 1,
  },
  title: {
    color: colors.text,
    fontSize: 18,
    lineHeight: 24,
    fontWeight: "800",
    marginBottom: 8,
  },
  metaRow: {
    flexDirection: "row",
    alignItems: "center",
    marginBottom: 6,
  },
  metaText: {
    color: colors.textSoft,
    fontSize: 13,
    fontWeight: "600",
    marginLeft: 7,
  },
  description: {
    color: colors.textMuted,
    fontSize: 14,
    lineHeight: 22,
    marginTop: spacing.sm,
  },
});
