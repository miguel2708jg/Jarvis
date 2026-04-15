import React, { useCallback, useState } from "react";
import {
  ActivityIndicator,
  Alert,
  FlatList,
  KeyboardAvoidingView,
  Modal,
  Platform,
  RefreshControl,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  TouchableOpacity,
  View,
} from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { useFocusEffect } from "@react-navigation/native";
import { Ionicons } from "@expo/vector-icons";

import type { Todo } from "../api/types";
import ModuleHero from "../components/ModuleHero";
import ScreenBackground from "../components/ScreenBackground";
import { useTodos } from "../hooks/useJarvisApi";
import { colors, radii, shadows, spacing } from "../theme/tokens";

type TodoDraft = {
  text: string;
  priority: Todo["priority"];
  due_date: string;
};

type TodoFilter = "pending" | "all" | "completed";

const EMPTY_DRAFT: TodoDraft = {
  text: "",
  priority: "medium",
  due_date: "",
};

const PRIORITY_META: Record<Todo["priority"], { label: string; color: string; background: string }> = {
  high: { label: "High", color: colors.danger, background: colors.dangerSoft },
  medium: { label: "Medium", color: "#A86B11", background: colors.amberSoft },
  low: { label: "Low", color: colors.success, background: colors.successSoft },
};

function formatDate(value: string): string {
  return new Date(value).toLocaleDateString(undefined, {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
}

function normalizeDueDate(value: string): string | null {
  const trimmed = value.trim();
  return trimmed ? trimmed : null;
}

export default function TodosScreen() {
  const {
    items: todos,
    loading,
    error,
    refresh,
    create,
    update,
    remove,
    setCompleted,
  } = useTodos();
  const [filter, setFilter] = useState<TodoFilter>("pending");
  const [draft, setDraft] = useState<TodoDraft>(EMPTY_DRAFT);
  const [editingTodo, setEditingTodo] = useState<Todo | null>(null);
  const [isModalVisible, setIsModalVisible] = useState(false);
  const [isSaving, setIsSaving] = useState(false);

  useFocusEffect(
    useCallback(() => {
      refresh({ show_completed: true });
    }, [refresh])
  );

  const pendingCount = todos.filter((todo) => !todo.completed).length;
  const completedCount = todos.filter((todo) => todo.completed).length;
  const overdueCount = todos.filter(
    (todo) => Boolean(todo.due_date) && !todo.completed && new Date(todo.due_date as string).getTime() < Date.now()
  ).length;

  const filteredTodos = todos.filter((todo) => {
    if (filter === "pending") {
      return !todo.completed;
    }
    if (filter === "completed") {
      return todo.completed;
    }
    return true;
  });

  const closeModal = useCallback(() => {
    setIsModalVisible(false);
    setEditingTodo(null);
    setDraft(EMPTY_DRAFT);
  }, []);

  const openCreateModal = useCallback(() => {
    setEditingTodo(null);
    setDraft(EMPTY_DRAFT);
    setIsModalVisible(true);
  }, []);

  const openEditModal = useCallback((todo: Todo) => {
    setEditingTodo(todo);
    setDraft({
      text: todo.text,
      priority: todo.priority,
      due_date: todo.due_date ? todo.due_date.slice(0, 10) : "",
    });
    setIsModalVisible(true);
  }, []);

  const handleDelete = useCallback((todo: Todo) => {
    Alert.alert("Delete ToDo", `Delete "${todo.text}"?`, [
      { text: "Cancel", style: "cancel" },
      {
        text: "Delete",
        style: "destructive",
        onPress: async () => {
          const deleted = await remove(todo.id);
          if (!deleted) {
            Alert.alert("Delete failed", "The ToDo could not be deleted.");
          }
        },
      },
    ]);
  }, [remove]);

  const handleToggle = useCallback(async (todo: Todo) => {
    const updated = await setCompleted(todo.id, !todo.completed);
    if (!updated) {
      Alert.alert("Update failed", "The ToDo status could not be changed.");
    }
  }, [setCompleted]);

  const handleSave = useCallback(async () => {
    const text = draft.text.trim();
    if (!text) {
      Alert.alert("Missing data", "ToDo text is required.");
      return;
    }

    setIsSaving(true);
    const payload = {
      text,
      priority: draft.priority,
      due_date: normalizeDueDate(draft.due_date),
      completed: editingTodo?.completed,
    };

    const saved = editingTodo ? await update(editingTodo.id, payload) : await create(payload);

    setIsSaving(false);
    if (saved) {
      closeModal();
    }
  }, [closeModal, create, draft.due_date, draft.priority, draft.text, editingTodo, update]);

  const renderHeader = () => (
    <View>
      <ModuleHero
        eyebrow="ToDo Board"
        title="Daily execution with more signal and less clutter."
        subtitle="Track work from chat or directly here. Priorities, due dates, and completion state stay readable at a glance."
        actionLabel="New ToDo"
        onActionPress={openCreateModal}
        stats={[
          { label: "Pending", value: String(pendingCount) },
          { label: "Completed", value: String(completedCount) },
          { label: "Overdue", value: String(overdueCount) },
        ]}
        error={error}
      >
        <View style={styles.filterRow}>
          {(["pending", "all", "completed"] as TodoFilter[]).map((value) => (
            <TouchableOpacity
              key={value}
              style={[styles.filterChip, filter === value && styles.filterChipActive]}
              onPress={() => setFilter(value)}
            >
              <Text style={[styles.filterChipText, filter === value && styles.filterChipTextActive]}>
                {value === "all" ? "All" : value === "pending" ? "Pending" : "Completed"}
              </Text>
            </TouchableOpacity>
          ))}
        </View>
      </ModuleHero>
    </View>
  );

  if (loading && todos.length === 0) {
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
        data={filteredTodos}
        keyExtractor={(item) => item.id}
        keyboardShouldPersistTaps="handled"
        contentContainerStyle={styles.list}
        refreshControl={
          <RefreshControl
            refreshing={loading}
            onRefresh={() => refresh({ show_completed: true })}
            tintColor={colors.accentStrong}
          />
        }
        ListHeaderComponent={renderHeader}
        ListEmptyComponent={
          <View style={styles.emptyCard}>
            <Text style={styles.emptyTitle}>No ToDos in this filter.</Text>
            <Text style={styles.emptyText}>
              Add one manually or ask Jarvis to turn your next plan into concrete ToDos.
            </Text>
          </View>
        }
        renderItem={({ item }) => {
          const priority = PRIORITY_META[item.priority];
          const isOverdue =
            Boolean(item.due_date) &&
            !item.completed &&
            new Date(item.due_date as string).getTime() < Date.now();

          return (
            <View style={[styles.card, item.completed && styles.cardCompleted]}>
              <TouchableOpacity style={styles.statusButton} onPress={() => handleToggle(item)}>
                <Ionicons
                  name={item.completed ? "checkmark-circle" : "ellipse-outline"}
                  size={28}
                  color={item.completed ? colors.success : colors.textSoft}
                />
              </TouchableOpacity>

              <TouchableOpacity
                style={styles.cardBody}
                onPress={() => openEditModal(item)}
                onLongPress={() => handleDelete(item)}
              >
                <View style={styles.cardHeader}>
                  <Text style={[styles.text, item.completed && styles.strikethrough]}>{item.text}</Text>
                  <View style={[styles.priorityBadge, { backgroundColor: priority.background }]}>
                    <Text style={[styles.priorityText, { color: priority.color }]}>{priority.label}</Text>
                  </View>
                </View>

                <View style={styles.metaRow}>
                  <View style={styles.metaGroup}>
                    <Ionicons
                      name="calendar-outline"
                      size={14}
                      color={isOverdue ? colors.danger : colors.textSoft}
                    />
                    <Text style={[styles.metaText, isOverdue && styles.overdueText]}>
                      {item.due_date ? `Due ${formatDate(item.due_date)}` : "No due date"}
                    </Text>
                  </View>

                  <View style={styles.metaGroup}>
                    <Ionicons name="time-outline" size={14} color={colors.textSoft} />
                    <Text style={styles.metaText}>Created {formatDate(item.created_at)}</Text>
                  </View>
                </View>
              </TouchableOpacity>
            </View>
          );
        }}
      />

      <Modal animationType="slide" transparent visible={isModalVisible} onRequestClose={closeModal}>
        <KeyboardAvoidingView
          style={styles.modalOverlay}
          behavior={Platform.OS === "ios" ? "padding" : undefined}
        >
          <View style={styles.modalCard}>
            <View style={styles.modalHandle} />
            <ScrollView contentContainerStyle={styles.modalBody} keyboardShouldPersistTaps="handled">
              <Text style={styles.modalEyebrow}>{editingTodo ? "Edit ToDo" : "Create ToDo"}</Text>
              <Text style={styles.modalTitle}>
                {editingTodo ? "Adjust the ToDo without losing momentum." : "Turn intent into a ToDo with structure."}
              </Text>

              <Text style={styles.inputLabel}>ToDo</Text>
              <TextInput
                style={[styles.input, styles.taskInput]}
                value={draft.text}
                onChangeText={(text) => setDraft((current) => ({ ...current, text }))}
                placeholder="Finish the presentation"
                placeholderTextColor={colors.textSoft}
                multiline
              />

              <Text style={styles.inputLabel}>Priority</Text>
              <View style={styles.priorityRow}>
                {(["low", "medium", "high"] as Todo["priority"][]).map((value) => {
                  const meta = PRIORITY_META[value];
                  const isSelected = draft.priority === value;

                  return (
                    <TouchableOpacity
                      key={value}
                      style={[
                        styles.priorityOption,
                        isSelected && {
                          borderColor: meta.color,
                          backgroundColor: meta.background,
                        },
                      ]}
                      onPress={() => setDraft((current) => ({ ...current, priority: value }))}
                    >
                      <Text
                        style={[
                          styles.priorityOptionText,
                          isSelected && { color: meta.color },
                        ]}
                      >
                        {meta.label}
                      </Text>
                    </TouchableOpacity>
                  );
                })}
              </View>

              <Text style={styles.inputLabel}>Due date</Text>
              <TextInput
                style={styles.input}
                value={draft.due_date}
                onChangeText={(due_date) => setDraft((current) => ({ ...current, due_date }))}
                placeholder="YYYY-MM-DD or full ISO datetime"
                placeholderTextColor={colors.textSoft}
                autoCapitalize="none"
              />
            </ScrollView>

            <View style={styles.modalActions}>
              <TouchableOpacity style={styles.secondaryButton} onPress={closeModal}>
                <Text style={styles.secondaryButtonText}>Cancel</Text>
              </TouchableOpacity>
              <TouchableOpacity
                style={[styles.primaryButton, isSaving && styles.disabledButton]}
                onPress={handleSave}
                disabled={isSaving}
              >
                <Text style={styles.primaryButtonText}>
                  {isSaving ? "Saving..." : editingTodo ? "Save changes" : "Create ToDo"}
                </Text>
              </TouchableOpacity>
            </View>
          </View>
        </KeyboardAvoidingView>
      </Modal>
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
  filterRow: {
    flexDirection: "row",
    flexWrap: "wrap",
    marginTop: spacing.md,
  },
  filterChip: {
    borderRadius: radii.pill,
    borderWidth: 1,
    borderColor: "rgba(255, 255, 255, 0.18)",
    paddingHorizontal: 12,
    paddingVertical: 8,
    marginRight: 8,
    marginBottom: 8,
  },
  filterChipActive: {
    backgroundColor: colors.white,
    borderColor: colors.white,
  },
  filterChipText: {
    fontSize: 13,
    fontWeight: "700",
    color: "rgba(255, 255, 255, 0.78)",
  },
  filterChipTextActive: {
    color: colors.ink,
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
    alignItems: "stretch",
    backgroundColor: colors.surface,
    borderRadius: radii.lg,
    padding: spacing.md,
    marginBottom: 14,
    borderWidth: 1,
    borderColor: colors.border,
    ...shadows.soft,
  },
  cardCompleted: {
    opacity: 0.7,
  },
  statusButton: {
    paddingRight: spacing.sm,
    justifyContent: "center",
  },
  cardBody: {
    flex: 1,
  },
  cardHeader: {
    flexDirection: "row",
    alignItems: "flex-start",
  },
  text: {
    flex: 1,
    marginRight: spacing.sm,
    fontSize: 16,
    lineHeight: 23,
    fontWeight: "700",
    color: colors.text,
  },
  strikethrough: {
    textDecorationLine: "line-through",
    color: colors.textSoft,
  },
  priorityBadge: {
    borderRadius: radii.pill,
    paddingHorizontal: 10,
    paddingVertical: 6,
  },
  priorityText: {
    fontSize: 12,
    fontWeight: "800",
  },
  metaRow: {
    marginTop: spacing.md,
  },
  metaGroup: {
    flexDirection: "row",
    alignItems: "center",
    marginBottom: 6,
  },
  metaText: {
    fontSize: 12,
    color: colors.textSoft,
    marginLeft: 6,
    fontWeight: "600",
  },
  overdueText: {
    color: colors.danger,
  },
  modalOverlay: {
    flex: 1,
    justifyContent: "flex-end",
    backgroundColor: colors.overlay,
  },
  modalCard: {
    backgroundColor: colors.surface,
    borderTopLeftRadius: 28,
    borderTopRightRadius: 28,
    maxHeight: "92%",
  },
  modalHandle: {
    width: 54,
    height: 5,
    borderRadius: 999,
    backgroundColor: colors.border,
    alignSelf: "center",
    marginTop: 10,
  },
  modalBody: {
    padding: spacing.xl,
    paddingBottom: spacing.md,
  },
  modalEyebrow: {
    color: colors.accentStrong,
    fontSize: 12,
    fontWeight: "800",
    letterSpacing: 1.3,
    textTransform: "uppercase",
    marginBottom: spacing.xs,
  },
  modalTitle: {
    color: colors.text,
    fontSize: 24,
    lineHeight: 30,
    fontWeight: "800",
    marginBottom: spacing.lg,
  },
  inputLabel: {
    fontSize: 13,
    fontWeight: "800",
    color: colors.text,
    marginBottom: 7,
  },
  input: {
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: radii.md,
    paddingHorizontal: 15,
    paddingVertical: 13,
    fontSize: 15,
    color: colors.text,
    backgroundColor: colors.backgroundMuted,
    marginBottom: spacing.md,
  },
  taskInput: {
    minHeight: 110,
    textAlignVertical: "top",
  },
  priorityRow: {
    flexDirection: "row",
    marginBottom: spacing.md,
  },
  priorityOption: {
    flex: 1,
    borderRadius: radii.md,
    borderWidth: 1,
    borderColor: colors.border,
    paddingVertical: 13,
    alignItems: "center",
    marginRight: 10,
    backgroundColor: colors.backgroundMuted,
  },
  priorityOptionText: {
    fontSize: 14,
    fontWeight: "800",
    color: colors.textMuted,
  },
  modalActions: {
    flexDirection: "row",
    paddingHorizontal: spacing.xl,
    paddingBottom: 30,
  },
  secondaryButton: {
    flex: 1,
    borderRadius: radii.md,
    borderWidth: 1,
    borderColor: colors.border,
    paddingVertical: 15,
    alignItems: "center",
    marginRight: 12,
    backgroundColor: colors.backgroundMuted,
  },
  secondaryButtonText: {
    fontSize: 15,
    fontWeight: "700",
    color: colors.textMuted,
  },
  primaryButton: {
    flex: 1.3,
    borderRadius: radii.md,
    backgroundColor: colors.ink,
    paddingVertical: 15,
    alignItems: "center",
  },
  primaryButtonText: {
    fontSize: 15,
    fontWeight: "800",
    color: colors.white,
  },
  disabledButton: {
    opacity: 0.6,
  },
});
