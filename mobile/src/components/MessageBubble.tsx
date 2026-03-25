import React from "react";
import { View, Text, StyleSheet } from "react-native";
import type { ChatMessage } from "../api/types";
import TypingIndicator from "./TypingIndicator";

interface Props {
  message: ChatMessage;
}

export default function MessageBubble({ message }: Props) {
  const isUser = message.role === "user";

  return (
    <View style={[styles.row, isUser ? styles.rowRight : styles.rowLeft]}>
      <View style={[styles.bubble, isUser ? styles.userBubble : styles.aiBubble]}>
        {message.isStreaming && message.content === "" ? (
          <TypingIndicator />
        ) : (
          <Text style={[styles.text, isUser ? styles.userText : styles.aiText]}>
            {message.content}
          </Text>
        )}
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  row: {
    marginVertical: 4,
    marginHorizontal: 12,
    flexDirection: "row",
  },
  rowRight: { justifyContent: "flex-end" },
  rowLeft: { justifyContent: "flex-start" },
  bubble: {
    maxWidth: "80%",
    borderRadius: 18,
    paddingHorizontal: 14,
    paddingVertical: 10,
  },
  userBubble: { backgroundColor: "#007AFF" },
  aiBubble: { backgroundColor: "#F2F2F7" },
  text: { fontSize: 16, lineHeight: 22 },
  userText: { color: "#FFFFFF" },
  aiText: { color: "#1C1C1E" },
});
