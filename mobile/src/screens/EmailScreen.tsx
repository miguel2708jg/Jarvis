import React, { useCallback, useState } from "react";
import {
  ActivityIndicator,
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

import { apiClient } from "../api/client";
import type { EmailMessage } from "../api/types";
import ModuleHero from "../components/ModuleHero";
import ScreenBackground from "../components/ScreenBackground";
import { colors, radii, shadows, spacing } from "../theme/tokens";

export default function EmailScreen() {
  const [emails, setEmails] = useState<EmailMessage[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchEmails = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const { data } = await apiClient.get<EmailMessage[]>("/emails");
      setEmails(data);
    } catch (err: any) {
      setError(err?.response?.data?.detail ?? err.message ?? "Failed to load emails");
    } finally {
      setLoading(false);
    }
  }, []);

  useFocusEffect(
    useCallback(() => {
      fetchEmails();
    }, [fetchEmails])
  );

  const unreadCount = emails.filter((email) => !email.is_read).length;

  if (loading && emails.length === 0) {
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
        data={emails}
        keyExtractor={(email) => email.message_id}
        contentContainerStyle={styles.list}
        refreshControl={
          <RefreshControl refreshing={loading} onRefresh={fetchEmails} tintColor={colors.accentStrong} />
        }
        ListHeaderComponent={
          <ModuleHero
            eyebrow="Inbox"
            title="Email should feel triaged before you even open a thread."
            subtitle="Use Jarvis to summarize the inbox, then drop here for a cleaner scan of sender, subject, urgency, and unread state."
            stats={[
              { label: "Messages", value: String(emails.length) },
              { label: "Unread", value: String(unreadCount) },
            ]}
            error={error}
          >
            <View style={styles.heroHintRow}>
              <View style={styles.heroHintChip}>
                <Ionicons name="mail-unread-outline" size={14} color={colors.accentStrong} />
                <Text style={styles.heroHintText}>Pull to refresh the inbox</Text>
              </View>
            </View>
          </ModuleHero>
        }
        ListEmptyComponent={
          <View style={styles.emptyCard}>
            <Text style={styles.emptyTitle}>No emails available.</Text>
            <Text style={styles.emptyText}>
              Configure Gmail credentials to enable inbox access, then ask Jarvis to summarize what matters.
            </Text>
            {error ? (
              <TouchableOpacity onPress={fetchEmails} style={styles.retryButton}>
                <Text style={styles.retryText}>Retry inbox sync</Text>
              </TouchableOpacity>
            ) : null}
          </View>
        }
        renderItem={({ item }) => (
          <TouchableOpacity style={[styles.card, !item.is_read && styles.cardUnread]}>
            <View style={styles.row}>
              <View style={styles.senderBlock}>
                <View style={[styles.readMarker, !item.is_read && styles.unreadMarker]} />
                <Text style={styles.sender} numberOfLines={1}>
                  {item.sender}
                </Text>
              </View>
              <Text style={styles.date}>{item.date}</Text>
            </View>

            <Text style={styles.subject} numberOfLines={1}>
              {item.subject || "(No subject)"}
            </Text>
            <Text style={styles.snippet} numberOfLines={3}>
              {item.snippet || item.body}
            </Text>

            <View style={styles.footerRow}>
              <View style={[styles.statusChip, !item.is_read && styles.statusChipUnread]}>
                <Text style={[styles.statusChipText, !item.is_read && styles.statusChipTextUnread]}>
                  {item.is_read ? "Read" : "Unread"}
                </Text>
              </View>
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
    backgroundColor: "rgba(255, 255, 255, 0.12)",
    paddingHorizontal: 12,
    paddingVertical: 9,
  },
  heroHintText: {
    color: colors.white,
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
  retryButton: {
    marginTop: spacing.lg,
    alignSelf: "flex-start",
    borderRadius: radii.pill,
    backgroundColor: colors.ink,
    paddingHorizontal: 16,
    paddingVertical: 10,
  },
  retryText: {
    color: colors.white,
    fontSize: 13,
    fontWeight: "800",
  },
  card: {
    backgroundColor: colors.surface,
    borderRadius: radii.lg,
    padding: spacing.lg,
    marginBottom: 12,
    borderWidth: 1,
    borderColor: colors.border,
    ...shadows.soft,
  },
  cardUnread: {
    borderColor: "#C2EDF2",
    backgroundColor: "#FCFFFE",
  },
  row: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: 8,
  },
  senderBlock: {
    flexDirection: "row",
    alignItems: "center",
    flex: 1,
    marginRight: spacing.sm,
  },
  readMarker: {
    width: 8,
    height: 8,
    borderRadius: 999,
    backgroundColor: colors.surfaceStrong,
    marginRight: 8,
  },
  unreadMarker: {
    backgroundColor: colors.accent,
  },
  sender: {
    fontWeight: "800",
    fontSize: 15,
    color: colors.text,
    flex: 1,
  },
  date: {
    fontSize: 12,
    color: colors.textSoft,
    fontWeight: "600",
  },
  subject: {
    fontSize: 16,
    lineHeight: 22,
    color: colors.text,
    fontWeight: "700",
    marginBottom: 6,
  },
  snippet: {
    fontSize: 14,
    lineHeight: 22,
    color: colors.textMuted,
  },
  footerRow: {
    flexDirection: "row",
    marginTop: spacing.md,
  },
  statusChip: {
    borderRadius: radii.pill,
    backgroundColor: colors.backgroundMuted,
    paddingHorizontal: 11,
    paddingVertical: 7,
  },
  statusChipUnread: {
    backgroundColor: colors.accentSoft,
  },
  statusChipText: {
    color: colors.textMuted,
    fontSize: 12,
    fontWeight: "700",
  },
  statusChipTextUnread: {
    color: colors.accentStrong,
  },
});
