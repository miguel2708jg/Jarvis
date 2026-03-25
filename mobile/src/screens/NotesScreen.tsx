import React, { useEffect, useState } from "react";
import {
  View,
  Text,
  FlatList,
  TouchableOpacity,
  StyleSheet,
  Alert,
  ActivityIndicator,
} from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { useNotes } from "../hooks/useJarvisApi";

export default function NotesScreen() {
  const { items: notes, loading, refresh, remove } = useNotes();

  useEffect(() => {
    refresh();
  }, []);

  const handleDelete = (id: string, title: string) => {
    Alert.alert("Delete Note", `Delete "${title}"?`, [
      { text: "Cancel", style: "cancel" },
      { text: "Delete", style: "destructive", onPress: () => remove(id) },
    ]);
  };

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
        data={notes}
        keyExtractor={(n) => n.id}
        contentContainerStyle={styles.list}
        ListEmptyComponent={<Text style={styles.empty}>No notes yet. Ask Jarvis to create one!</Text>}
        renderItem={({ item }) => (
          <TouchableOpacity
            style={styles.card}
            onLongPress={() => handleDelete(item.id, item.title)}
          >
            <Text style={styles.title}>{item.title}</Text>
            <Text style={styles.content} numberOfLines={2}>{item.content}</Text>
            {item.tags.length > 0 && (
              <View style={styles.tags}>
                {item.tags.map((tag) => (
                  <View key={tag} style={styles.tag}>
                    <Text style={styles.tagText}>{tag}</Text>
                  </View>
                ))}
              </View>
            )}
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
    marginBottom: 12,
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.08,
    shadowRadius: 4,
    elevation: 2,
  },
  title: { fontSize: 17, fontWeight: "600", color: "#1C1C1E", marginBottom: 4 },
  content: { fontSize: 14, color: "#3C3C43", lineHeight: 20 },
  tags: { flexDirection: "row", marginTop: 8, flexWrap: "wrap" },
  tag: { backgroundColor: "#E5F0FF", borderRadius: 8, paddingHorizontal: 8, paddingVertical: 3, marginRight: 6 },
  tagText: { fontSize: 12, color: "#007AFF" },
});
