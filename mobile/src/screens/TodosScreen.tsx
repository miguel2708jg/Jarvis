import React, { useEffect } from "react";
import {
  View,
  Text,
  FlatList,
  TouchableOpacity,
  StyleSheet,
  ActivityIndicator,
} from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { useTodos } from "../hooks/useJarvisApi";

const PRIORITY_COLOR: Record<string, string> = {
  high: "#FF3B30",
  medium: "#FF9500",
  low: "#34C759",
};

export default function TodosScreen() {
  const { items: todos, loading, refresh, complete, remove } = useTodos();

  useEffect(() => {
    refresh();
  }, []);

  if (loading) {
    return (
      <View style={styles.center}>
        <ActivityIndicator size="large" color="#007AFF" />
      </View>
    );
  }

  return (
    <SafeAreaView style={styles.container} edges={["bottom"]}>
      <FlatList
        data={todos}
        keyExtractor={(t) => t.id}
        contentContainerStyle={styles.list}
        ListEmptyComponent={
          <Text style={styles.empty}>No todos. Ask Jarvis to add one!</Text>
        }
        renderItem={({ item }) => (
          <TouchableOpacity
            style={[styles.card, item.completed && styles.completed]}
            onPress={() => !item.completed && complete(item.id)}
            onLongPress={() => remove(item.id)}
          >
            <View style={styles.row}>
              <View style={[styles.dot, { backgroundColor: PRIORITY_COLOR[item.priority] }]} />
              <Text style={[styles.text, item.completed && styles.strikethrough]}>
                {item.text}
              </Text>
              {item.completed && <Text style={styles.checkmark}>✓</Text>}
            </View>
          </TouchableOpacity>
        )}
      />
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: "#F2F2F7" },
  center: { flex: 1, alignItems: "center", justifyContent: "center" },
  list: { padding: 16 },
  empty: { textAlign: "center", color: "#8E8E93", marginTop: 40, fontSize: 16 },
  card: {
    backgroundColor: "#FFFFFF",
    borderRadius: 12,
    padding: 16,
    marginBottom: 10,
  },
  completed: { opacity: 0.5 },
  row: { flexDirection: "row", alignItems: "center" },
  dot: { width: 10, height: 10, borderRadius: 5, marginRight: 10 },
  text: { flex: 1, fontSize: 16, color: "#1C1C1E" },
  strikethrough: { textDecorationLine: "line-through", color: "#8E8E93" },
  checkmark: { fontSize: 18, color: "#34C759" },
});
