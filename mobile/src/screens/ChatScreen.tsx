import React, { useRef, useState } from "react";
import {
  FlatList,
  KeyboardAvoidingView,
  Platform,
  StyleSheet,
  Text,
  TextInput,
  TouchableOpacity,
  View,
} from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { Ionicons } from "@expo/vector-icons";

import type { ToolActivity } from "../api/types";
import MessageBubble from "../components/MessageBubble";
import ScreenBackground from "../components/ScreenBackground";
import { useJarvisChat } from "../hooks/useJarvisChat";
import { colors, radii, shadows, spacing } from "../theme/tokens";

const QUICK_ACTIONS = [
  {
    label: "Plan my day",
    icon: "sparkles-outline" as const,
    prompt: "Plan my day using my notes, ToDos, calendar, and email.",
  },
  {
    label: "Create ToDo",
    icon: "checkmark-circle-outline" as const,
    prompt: "Create a high priority ToDo to follow up on everything urgent today.",
  },
  {
    label: "Summarize notes",
    icon: "document-text-outline" as const,
    prompt: "Summarize my notes into a short action-oriented brief.",
  },
  {
    label: "Check email",
    icon: "mail-outline" as const,
    prompt: "Review my latest emails and highlight anything that needs a reply.",
  },
];

function formatToolName(value: string): string {
  return value
    .split("_")
    .map((part) => {
      if (part.toLowerCase() === "todo") {
        return "ToDo";
      }
      return part.charAt(0).toUpperCase() + part.slice(1);
    })
    .join(" ");
}

function getToolIcon(tool: string): React.ComponentProps<typeof Ionicons>["name"] {
  const normalized = tool.toLowerCase();

  if (normalized.includes("note")) {
    return "document-text-outline";
  }
  if (normalized.includes("todo") || normalized.includes("task")) {
    return "checkmark-circle-outline";
  }
  if (normalized.includes("calendar")) {
    return "calendar-outline";
  }
  if (normalized.includes("email") || normalized.includes("mail")) {
    return "mail-outline";
  }
  return "sparkles-outline";
}

function ActivityCard({
  activeTools,
  lastCompletedTool,
  error,
}: {
  activeTools: ToolActivity[];
  lastCompletedTool: string | null;
  error: string | null;
}) {
  if (activeTools.length === 0 && !lastCompletedTool && !error) {
    return null;
  }

  return (
    <View style={styles.activityCard}>
      <View style={styles.activityHeader}>
        <Text style={styles.sectionEyebrow}>Live Activity</Text>
        <Text style={styles.activityTitle}>
          {activeTools.length > 0 ? "Jarvis is using tools" : "Latest assistant activity"}
        </Text>
      </View>

      {activeTools.length > 0 ? (
        <View style={styles.toolRow}>
          {activeTools.map((tool) => (
            <View key={tool.name} style={styles.toolChip}>
              <Ionicons name={getToolIcon(tool.name)} size={15} color={colors.accentStrong} />
              <Text style={styles.toolChipText}>{formatToolName(tool.name)}</Text>
            </View>
          ))}
        </View>
      ) : null}

      {activeTools.length === 0 && lastCompletedTool ? (
        <View style={styles.completedChip}>
          <Ionicons name="checkmark-circle" size={16} color={colors.success} />
          <Text style={styles.completedChipText}>
            {formatToolName(lastCompletedTool)} finished successfully
          </Text>
        </View>
      ) : null}

      {error ? <Text style={styles.errorBanner}>{error}</Text> : null}
    </View>
  );
}

export default function ChatScreen() {
  const [input, setInput] = useState("");
  const {
    messages,
    sendMessage,
    isConnected,
    isStreaming,
    activeTools,
    lastCompletedTool,
    error,
  } = useJarvisChat();
  const listRef = useRef<FlatList>(null);

  const handleSend = () => {
    const text = input.trim();
    if (!text || isStreaming || !isConnected) {
      return;
    }

    setInput("");
    sendMessage(text);
  };

  const runQuickAction = (prompt: string) => {
    if (!isConnected || isStreaming) {
      return;
    }

    setInput("");
    sendMessage(prompt);
  };

  const renderHeader = () => (
    <View>
      <View style={styles.heroCard}>
        <View style={styles.heroGlow} />
        <Text style={styles.heroEyebrow}>Personal AI Operator</Text>

        <View style={styles.heroTopRow}>
          <View style={styles.heroCopy}>
            <Text style={styles.heroTitle}>Jarvis keeps your workday aligned.</Text>
            <Text style={styles.heroSubtitle}>
              Ask for plans, summarize context, or let the assistant touch notes, ToDos,
              calendar, and email without leaving chat.
            </Text>
          </View>

          <View style={[styles.connectionPill, isConnected ? styles.onlinePill : styles.offlinePill]}>
            <View style={[styles.connectionDot, isConnected ? styles.onlineDot : styles.offlineDot]} />
            <Text style={styles.connectionText}>{isConnected ? "Connected" : "Connecting"}</Text>
          </View>
        </View>

        <View style={styles.heroMetricRow}>
          <View style={styles.metricCard}>
            <Text style={styles.metricValue}>5</Text>
            <Text style={styles.metricLabel}>Core modules</Text>
          </View>
          <View style={styles.metricCard}>
            <Text style={styles.metricValue}>Live</Text>
            <Text style={styles.metricLabel}>Streaming replies</Text>
          </View>
          <View style={styles.metricCard}>
            <Text style={styles.metricValue}>Tools</Text>
            <Text style={styles.metricLabel}>Action-aware chat</Text>
          </View>
        </View>
      </View>

      {messages.length === 0 ? (
        <View style={styles.emptyCard}>
          <Text style={styles.sectionEyebrow}>Start Here</Text>
          <Text style={styles.emptyTitle}>Use Jarvis like an operator, not a chatbot.</Text>
          <Text style={styles.emptyText}>
            Give it goals, context, and constraints. It already understands your productivity
            surfaces and can route work across them.
          </Text>
        </View>
      ) : null}

      <View style={styles.quickActionsBlock}>
        <Text style={styles.sectionEyebrow}>Quick Actions</Text>
        <Text style={styles.sectionTitle}>Push the assistant into useful flows fast.</Text>

        <View style={styles.quickActionsGrid}>
          {QUICK_ACTIONS.map((action) => (
            <TouchableOpacity
              key={action.label}
              style={styles.quickActionCard}
              onPress={() => runQuickAction(action.prompt)}
              disabled={!isConnected || isStreaming}
            >
              <View style={styles.quickActionIcon}>
                <Ionicons name={action.icon} size={18} color={colors.accentStrong} />
              </View>
              <Text style={styles.quickActionText}>{action.label}</Text>
            </TouchableOpacity>
          ))}
        </View>
      </View>

      <ActivityCard
        activeTools={activeTools}
        lastCompletedTool={lastCompletedTool}
        error={error}
      />
    </View>
  );

  return (
    <SafeAreaView style={styles.container} edges={["top"]}>
      <ScreenBackground />

      <KeyboardAvoidingView
        style={styles.flex}
        behavior={Platform.OS === "ios" ? "padding" : undefined}
        keyboardVerticalOffset={10}
      >
        <FlatList
          ref={listRef}
          data={messages}
          keyExtractor={(message) => message.id}
          renderItem={({ item }) => <MessageBubble message={item} />}
          onContentSizeChange={() => listRef.current?.scrollToEnd({ animated: true })}
          contentContainerStyle={styles.list}
          ListHeaderComponent={renderHeader}
          ListFooterComponent={<View style={styles.listFooter} />}
          keyboardShouldPersistTaps="handled"
          showsVerticalScrollIndicator={false}
        />

        <View style={styles.composerWrap}>
          <View style={styles.composerShell}>
            <TextInput
              style={styles.input}
              value={input}
              onChangeText={setInput}
              placeholder={isConnected ? "Ask Jarvis to organize the next move" : "Waiting for connection"}
              placeholderTextColor={colors.textSoft}
              multiline
              returnKeyType="send"
              onSubmitEditing={handleSend}
              editable={isConnected}
            />

            <TouchableOpacity
              onPress={handleSend}
              style={[styles.sendButton, (!isConnected || isStreaming) && styles.sendButtonDisabled]}
              disabled={!isConnected || isStreaming}
            >
              <Ionicons name="arrow-up" size={18} color={colors.white} />
            </TouchableOpacity>
          </View>

          <Text style={styles.composerHint}>
            {isStreaming
              ? "Jarvis is responding and may call tools while it thinks."
              : isConnected
                ? "Chat is live. Tool activity appears above while Jarvis works."
                : "Connecting to the local assistant backend."}
          </Text>
        </View>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  flex: {
    flex: 1,
  },
  container: {
    flex: 1,
    backgroundColor: colors.background,
  },
  list: {
    paddingHorizontal: spacing.md,
    paddingTop: spacing.md,
  },
  listFooter: {
    height: 16,
  },
  heroCard: {
    position: "relative",
    overflow: "hidden",
    backgroundColor: colors.ink,
    borderRadius: radii.xl,
    padding: spacing.xl,
    marginBottom: spacing.lg,
    ...shadows.card,
  },
  heroGlow: {
    position: "absolute",
    width: 200,
    height: 200,
    borderRadius: 999,
    top: -90,
    right: -20,
    backgroundColor: "rgba(27, 183, 199, 0.24)",
  },
  heroEyebrow: {
    color: "#99ECF5",
    fontSize: 11,
    fontWeight: "800",
    letterSpacing: 1.7,
    textTransform: "uppercase",
    marginBottom: spacing.md,
  },
  heroTopRow: {
    flexDirection: "row",
    alignItems: "flex-start",
    justifyContent: "space-between",
  },
  heroCopy: {
    flex: 1,
    paddingRight: spacing.md,
  },
  heroTitle: {
    color: colors.white,
    fontSize: 30,
    lineHeight: 34,
    fontWeight: "800",
    marginBottom: spacing.sm,
  },
  heroSubtitle: {
    color: "rgba(255, 255, 255, 0.75)",
    fontSize: 14,
    lineHeight: 22,
  },
  connectionPill: {
    flexDirection: "row",
    alignItems: "center",
    paddingHorizontal: 12,
    paddingVertical: 10,
    borderRadius: radii.pill,
  },
  onlinePill: {
    backgroundColor: "rgba(255, 255, 255, 0.14)",
  },
  offlinePill: {
    backgroundColor: "rgba(255, 255, 255, 0.08)",
  },
  connectionDot: {
    width: 8,
    height: 8,
    borderRadius: 999,
    marginRight: 8,
  },
  onlineDot: {
    backgroundColor: "#6CE4AE",
  },
  offlineDot: {
    backgroundColor: colors.amber,
  },
  connectionText: {
    color: colors.white,
    fontSize: 12,
    fontWeight: "700",
  },
  heroMetricRow: {
    flexDirection: "row",
    marginTop: spacing.lg,
  },
  metricCard: {
    flex: 1,
    backgroundColor: "rgba(255, 255, 255, 0.12)",
    borderRadius: radii.md,
    padding: 14,
    marginRight: spacing.sm,
  },
  metricValue: {
    color: colors.white,
    fontSize: 20,
    fontWeight: "800",
    marginBottom: 4,
  },
  metricLabel: {
    color: "rgba(255, 255, 255, 0.68)",
    fontSize: 12,
    lineHeight: 18,
    fontWeight: "600",
  },
  emptyCard: {
    backgroundColor: colors.surface,
    borderRadius: radii.lg,
    padding: spacing.lg,
    marginBottom: spacing.lg,
    borderWidth: 1,
    borderColor: colors.border,
    ...shadows.soft,
  },
  sectionEyebrow: {
    color: colors.accentStrong,
    fontSize: 11,
    fontWeight: "800",
    letterSpacing: 1.5,
    textTransform: "uppercase",
    marginBottom: spacing.xs,
  },
  sectionTitle: {
    color: colors.text,
    fontSize: 22,
    lineHeight: 27,
    fontWeight: "800",
    marginBottom: spacing.md,
  },
  emptyTitle: {
    color: colors.text,
    fontSize: 22,
    lineHeight: 27,
    fontWeight: "800",
    marginBottom: spacing.sm,
  },
  emptyText: {
    color: colors.textMuted,
    fontSize: 14,
    lineHeight: 22,
  },
  quickActionsBlock: {
    marginBottom: spacing.lg,
  },
  quickActionsGrid: {
    flexDirection: "row",
    flexWrap: "wrap",
    marginHorizontal: -6,
  },
  quickActionCard: {
    width: "50%",
    paddingHorizontal: 6,
    marginBottom: 12,
  },
  quickActionIcon: {
    width: 38,
    height: 38,
    borderRadius: 12,
    backgroundColor: colors.accentSoft,
    alignItems: "center",
    justifyContent: "center",
    marginBottom: 10,
  },
  quickActionText: {
    color: colors.text,
    fontSize: 14,
    fontWeight: "700",
  },
  activityCard: {
    backgroundColor: colors.surface,
    borderRadius: radii.lg,
    padding: spacing.lg,
    borderWidth: 1,
    borderColor: colors.border,
    ...shadows.soft,
  },
  activityHeader: {
    marginBottom: spacing.sm,
  },
  activityTitle: {
    color: colors.text,
    fontSize: 20,
    fontWeight: "800",
  },
  toolRow: {
    flexDirection: "row",
    flexWrap: "wrap",
    marginTop: spacing.sm,
  },
  toolChip: {
    flexDirection: "row",
    alignItems: "center",
    backgroundColor: colors.surfaceMuted,
    borderRadius: radii.pill,
    paddingHorizontal: 12,
    paddingVertical: 9,
    marginRight: 8,
    marginBottom: 8,
    borderWidth: 1,
    borderColor: colors.border,
  },
  toolChipText: {
    color: colors.text,
    fontSize: 13,
    fontWeight: "700",
    marginLeft: 8,
  },
  completedChip: {
    flexDirection: "row",
    alignItems: "center",
    backgroundColor: colors.successSoft,
    borderRadius: radii.pill,
    paddingHorizontal: 12,
    paddingVertical: 10,
    alignSelf: "flex-start",
    marginTop: spacing.sm,
  },
  completedChipText: {
    color: colors.success,
    fontSize: 13,
    fontWeight: "700",
    marginLeft: 8,
  },
  errorBanner: {
    marginTop: spacing.md,
    paddingHorizontal: 12,
    paddingVertical: 10,
    borderRadius: radii.sm,
    backgroundColor: colors.dangerSoft,
    color: colors.danger,
    fontSize: 13,
    fontWeight: "700",
  },
  composerWrap: {
    paddingHorizontal: spacing.md,
    paddingTop: spacing.sm,
    paddingBottom: 106,
    backgroundColor: "rgba(246, 241, 231, 0.96)",
  },
  composerShell: {
    flexDirection: "row",
    alignItems: "flex-end",
    backgroundColor: colors.surface,
    borderRadius: radii.lg,
    padding: 8,
    borderWidth: 1,
    borderColor: colors.border,
    ...shadows.soft,
  },
  input: {
    flex: 1,
    minHeight: 56,
    maxHeight: 132,
    paddingHorizontal: 14,
    paddingTop: 14,
    paddingBottom: 14,
    fontSize: 15,
    lineHeight: 22,
    color: colors.text,
  },
  sendButton: {
    width: 48,
    height: 48,
    borderRadius: 16,
    backgroundColor: colors.ink,
    alignItems: "center",
    justifyContent: "center",
  },
  sendButtonDisabled: {
    backgroundColor: colors.textSoft,
  },
  composerHint: {
    color: colors.textMuted,
    fontSize: 12,
    lineHeight: 18,
    marginTop: 10,
    paddingHorizontal: 4,
  },
});
