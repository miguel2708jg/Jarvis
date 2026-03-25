import React, { useEffect } from "react";
import {
  View,
  Text,
  FlatList,
  StyleSheet,
  ActivityIndicator,
  Alert,
  TouchableOpacity,
} from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { useCalendar } from "../hooks/useJarvisApi";

function formatDate(iso: string): string {
  const d = new Date(iso);
  return d.toLocaleString(undefined, {
    weekday: "short",
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export default function CalendarScreen() {
  const { items: events, loading, refresh, remove } = useCalendar();

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
        data={events}
        keyExtractor={(e) => e.id}
        contentContainerStyle={styles.list}
        ListEmptyComponent={
          <Text style={styles.empty}>No events. Ask Jarvis to schedule one!</Text>
        }
        renderItem={({ item }) => (
          <TouchableOpacity
            style={styles.card}
            onLongPress={() =>
              Alert.alert("Delete Event", `Delete "${item.title}"?`, [
                { text: "Cancel", style: "cancel" },
                { text: "Delete", style: "destructive", onPress: () => remove(item.id) },
              ])
            }
          >
            <View style={styles.accent} />
            <View style={styles.info}>
              <Text style={styles.title}>{item.title}</Text>
              <Text style={styles.time}>{formatDate(item.start_datetime)}</Text>
              {item.location ? (
                <Text style={styles.location}>📍 {item.location}</Text>
              ) : null}
              {item.description ? (
                <Text style={styles.description} numberOfLines={2}>
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
  container: { flex: 1, backgroundColor: "#F2F2F7" },
  center: { flex: 1, alignItems: "center", justifyContent: "center" },
  list: { padding: 16 },
  empty: { textAlign: "center", color: "#8E8E93", marginTop: 40, fontSize: 16 },
  card: {
    flexDirection: "row",
    backgroundColor: "#FFFFFF",
    borderRadius: 12,
    marginBottom: 12,
    overflow: "hidden",
  },
  accent: { width: 6, backgroundColor: "#007AFF" },
  info: { flex: 1, padding: 14 },
  title: { fontSize: 16, fontWeight: "600", color: "#1C1C1E" },
  time: { fontSize: 13, color: "#8E8E93", marginTop: 4 },
  location: { fontSize: 13, color: "#3C3C43", marginTop: 4 },
  description: { fontSize: 13, color: "#8E8E93", marginTop: 4 },
});
