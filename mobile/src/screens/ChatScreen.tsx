import React, { useState, useRef } from "react";
import {
  View,
  FlatList,
  TextInput,
  TouchableOpacity,
  StyleSheet,
  KeyboardAvoidingView,
  Platform,
  Text,
} from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import MessageBubble from "../components/MessageBubble";
import { useJarvisChat } from "../hooks/useJarvisChat";

export default function ChatScreen() {
  const [input, setInput] = useState("");
  const { messages, sendMessage, isConnected, isStreaming } = useJarvisChat();
  const listRef = useRef<FlatList>(null);

  const handleSend = () => {
    const text = input.trim();
    if (!text || isStreaming || !isConnected) return;
    setInput("");
    sendMessage(text);
  };

  return (
    <SafeAreaView style={styles.container} edges={["bottom"]}>
      <KeyboardAvoidingView
        style={styles.flex}
        behavior={Platform.OS === "ios" ? "padding" : undefined}
        keyboardVerticalOffset={90}
      >
        <FlatList
          ref={listRef}
          data={messages}
          keyExtractor={(m) => m.id}
          renderItem={({ item }) => <MessageBubble message={item} />}
          onContentSizeChange={() => listRef.current?.scrollToEnd({ animated: true })}
          contentContainerStyle={styles.list}
        />
        <View style={styles.inputRow}>
          <TextInput
            style={styles.input}
            value={input}
            onChangeText={setInput}
            placeholder={isConnected ? "Message Jarvis…" : "Connecting…"}
            placeholderTextColor="#8E8E93"
            multiline
            returnKeyType="send"
            onSubmitEditing={handleSend}
            editable={isConnected}
          />
          <TouchableOpacity
            onPress={handleSend}
            style={[styles.sendButton, (!isConnected || isStreaming) && styles.disabled]}
            disabled={!isConnected || isStreaming}
          >
            <Text style={styles.sendText}>↑</Text>
          </TouchableOpacity>
        </View>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  flex: { flex: 1 },
  container: { flex: 1, backgroundColor: "#FFFFFF" },
  list: { paddingVertical: 12 },
  inputRow: {
    flexDirection: "row",
    alignItems: "flex-end",
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderTopWidth: StyleSheet.hairlineWidth,
    borderTopColor: "#C6C6C8",
    backgroundColor: "#FFFFFF",
  },
  input: {
    flex: 1,
    minHeight: 40,
    maxHeight: 120,
    borderRadius: 20,
    backgroundColor: "#F2F2F7",
    paddingHorizontal: 16,
    paddingVertical: 10,
    fontSize: 16,
    color: "#1C1C1E",
    marginRight: 8,
  },
  sendButton: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: "#007AFF",
    alignItems: "center",
    justifyContent: "center",
  },
  disabled: { backgroundColor: "#C7C7CC" },
  sendText: { color: "#FFFFFF", fontSize: 20, fontWeight: "bold" },
});
