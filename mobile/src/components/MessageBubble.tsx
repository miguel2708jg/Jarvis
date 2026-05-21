import React from "react";
import { StyleSheet, Text, View } from "react-native";

import type { ChatMessage } from "../api/types";
import { colors, radii, shadows } from "../theme/tokens";
import StreamingText from "./StreamingText";
import TypingIndicator from "./TypingIndicator";

interface Props {
  message: ChatMessage;
}

export default function MessageBubble({ message }: Props) {
  const isUser = message.role === "user";

  return (
    <View style={[styles.row, isUser ? styles.rowRight : styles.rowLeft]}>
      {!isUser ? (
        <View style={styles.avatar}>
          <Text style={styles.avatarText}>J</Text>
        </View>
      ) : null}

      <View style={styles.stack}>
        <Text style={[styles.label, isUser ? styles.userLabel : styles.aiLabel]}>
          {isUser ? "You" : "Jarvis"}
        </Text>

        <View style={[styles.bubble, isUser ? styles.userBubble : styles.aiBubble]}>
          {message.isStreaming && message.content === "" ? (
            <TypingIndicator />
          ) : message.isStreaming ? (
            <StreamingText
              text={message.content}
              style={[styles.text, isUser ? styles.userText : styles.aiText]}
            />
          ) : (
            <Text style={[styles.text, isUser ? styles.userText : styles.aiText]}>
              {message.content}
            </Text>
          )}
        </View>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  row: {
    marginBottom: 16,
    marginHorizontal: 16,
    flexDirection: "row",
    alignItems: "flex-end",
  },
  rowRight: {
    justifyContent: "flex-end",
  },
  rowLeft: {
    justifyContent: "flex-start",
  },
  stack: {
    maxWidth: "82%",
  },
  avatar: {
    width: 30,
    height: 30,
    borderRadius: 15,
    alignItems: "center",
    justifyContent: "center",
    backgroundColor: colors.primaryStrong,
    marginRight: 10,
    marginBottom: 6,
  },
  avatarText: {
    color: colors.white,
    fontSize: 12,
    fontWeight: "800",
  },
  label: {
    fontSize: 11,
    fontWeight: "800",
    letterSpacing: 0.7,
    textTransform: "uppercase",
    marginBottom: 6,
    paddingHorizontal: 4,
  },
  aiLabel: {
    color: colors.textSoft,
  },
  userLabel: {
    color: colors.ink,
    textAlign: "right",
  },
  bubble: {
    borderRadius: radii.md,
    paddingHorizontal: 16,
    paddingVertical: 14,
  },
  userBubble: {
    backgroundColor: colors.warning,
    borderTopRightRadius: 6,
    borderWidth: 1,
    borderColor: "rgba(255, 255, 255, 0.62)",
  },
  aiBubble: {
    backgroundColor: colors.surface,
    borderTopLeftRadius: 6,
    borderWidth: 1,
    borderColor: colors.border,
    ...shadows.soft,
  },
  text: {
    fontSize: 15,
    lineHeight: 23,
  },
  userText: {
    color: colors.ink,
  },
  aiText: {
    color: colors.text,
  },
});
