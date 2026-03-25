import React, { useEffect, useState } from "react";
import {
  View,
  Text,
  FlatList,
  StyleSheet,
  ActivityIndicator,
  TouchableOpacity,
  Alert,
} from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { apiClient } from "../api/client";
import type { EmailMessage } from "../api/types";

export default function EmailScreen() {
  const [emails, setEmails] = useState<EmailMessage[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchEmails = async () => {
    setLoading(true);
    setError(null);
    try {
      const { data } = await apiClient.get<EmailMessage[]>("/emails");
      setEmails(data);
    } catch (e: any) {
      setError(e?.response?.data?.detail ?? e.message ?? "Failed to load emails");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchEmails();
  }, []);

  if (loading) {
    return (
      <View style={styles.center}>
        <ActivityIndicator size="large" color="#007AFF" />
      </View>
    );
  }

  if (error) {
    return (
      <View style={styles.center}>
        <Text style={styles.error}>{error}</Text>
        <TouchableOpacity onPress={fetchEmails} style={styles.retry}>
          <Text style={styles.retryText}>Retry</Text>
        </TouchableOpacity>
      </View>
    );
  }

  return (
    <SafeAreaView style={styles.container} edges={["bottom"]}>
      <FlatList
        data={emails}
        keyExtractor={(e) => e.message_id}
        contentContainerStyle={styles.list}
        ListEmptyComponent={
          <Text style={styles.empty}>No emails. Configure Gmail credentials to enable.</Text>
        }
        renderItem={({ item }) => (
          <TouchableOpacity style={styles.card}>
            <View style={styles.row}>
              <Text style={styles.sender} numberOfLines={1}>{item.sender}</Text>
              <Text style={styles.date}>{item.date}</Text>
            </View>
            <Text style={styles.subject} numberOfLines={1}>{item.subject}</Text>
            <Text style={styles.snippet} numberOfLines={2}>{item.snippet}</Text>
          </TouchableOpacity>
        )}
      />
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: "#F2F2F7" },
  center: { flex: 1, alignItems: "center", justifyContent: "center", padding: 20 },
  list: { padding: 16 },
  empty: { textAlign: "center", color: "#8E8E93", marginTop: 40, fontSize: 15 },
  error: { color: "#FF3B30", fontSize: 15, textAlign: "center", marginBottom: 16 },
  retry: { backgroundColor: "#007AFF", borderRadius: 8, paddingHorizontal: 20, paddingVertical: 10 },
  retryText: { color: "#FFFFFF", fontWeight: "600" },
  card: {
    backgroundColor: "#FFFFFF",
    borderRadius: 12,
    padding: 14,
    marginBottom: 10,
  },
  row: { flexDirection: "row", justifyContent: "space-between", marginBottom: 4 },
  sender: { fontWeight: "600", fontSize: 14, color: "#1C1C1E", flex: 1 },
  date: { fontSize: 12, color: "#8E8E93", marginLeft: 8 },
  subject: { fontSize: 15, color: "#1C1C1E", marginBottom: 4 },
  snippet: { fontSize: 13, color: "#8E8E93" },
});
