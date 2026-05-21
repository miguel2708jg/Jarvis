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
import { useFocusEffect } from "@react-navigation/native";
import { Ionicons } from "@expo/vector-icons";

import AppScreen from "../components/AppScreen";
import { EmptyState, ModalSheet, PrimaryButton, TextField } from "../components/design";
import type { Note } from "../api/types";
import ModuleHero from "../components/ModuleHero";
import { useKnowledge, useNotes } from "../hooks/useJarvisApi";
import { colors, radii, shadows, spacing } from "../theme/tokens";

type NoteDraft = {
  title: string;
  content: string;
  tags: string;
};

const EMPTY_DRAFT: NoteDraft = {
  title: "",
  content: "",
  tags: "",
};

function formatDate(value: string): string {
  return new Date(value).toLocaleString(undefined, {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function parseTags(value: string): string[] {
  return value
    .split(",")
    .map((tag) => tag.trim())
    .filter(Boolean);
}

export default function NotesScreen() {
  const { items: notes, loading, error, refresh, create, update, remove } = useNotes();
  const { ingestNote } = useKnowledge();
  const [draft, setDraft] = useState<NoteDraft>(EMPTY_DRAFT);
  const [editingNote, setEditingNote] = useState<Note | null>(null);
  const [isModalVisible, setIsModalVisible] = useState(false);
  const [isSaving, setIsSaving] = useState(false);

  useFocusEffect(
    useCallback(() => {
      refresh();
    }, [refresh])
  );

  const taggedNotes = notes.filter((note) => note.tags.length > 0).length;
  const latestNote = notes[0];

  const closeModal = useCallback(() => {
    setIsModalVisible(false);
    setEditingNote(null);
    setDraft(EMPTY_DRAFT);
  }, []);

  const openCreateModal = useCallback(() => {
    setEditingNote(null);
    setDraft(EMPTY_DRAFT);
    setIsModalVisible(true);
  }, []);

  const openEditModal = useCallback((note: Note) => {
    setEditingNote(note);
    setDraft({
      title: note.title,
      content: note.content,
      tags: note.tags.join(", "),
    });
    setIsModalVisible(true);
  }, []);

  const handleDelete = useCallback((note: Note) => {
    Alert.alert("Delete note", `Delete "${note.title}"?`, [
      { text: "Cancel", style: "cancel" },
      {
        text: "Delete",
        style: "destructive",
        onPress: async () => {
          const deleted = await remove(note.id);
          if (!deleted) {
            Alert.alert("Delete failed", "The note could not be deleted.");
          }
        },
      },
    ]);
  }, [remove]);

  const handleAddToKnowledge = useCallback(async (note: Note) => {
    const result = await ingestNote(note.id);
    if (!result) {
      Alert.alert("Ingest failed", "The note could not be added to the knowledge vault.");
      return;
    }
    Alert.alert("Knowledge updated", `${result.touched_pages.length} page(s) updated.`);
  }, [ingestNote]);

  const handleSave = useCallback(async () => {
    const title = draft.title.trim();
    const content = draft.content.trim();

    if (!title || !content) {
      Alert.alert("Missing data", "Title and content are required.");
      return;
    }

    setIsSaving(true);
    const payload = {
      title,
      content,
      tags: parseTags(draft.tags),
    };

    const saved = editingNote ? await update(editingNote.id, payload) : await create(payload);

    setIsSaving(false);
    if (saved) {
      closeModal();
    }
  }, [closeModal, create, draft.content, draft.tags, draft.title, editingNote, update]);

  const renderHeader = () => (
    <ModuleHero
      eyebrow="Notebook"
      title="Notes that look organized before you open them."
      subtitle="Keep personal context in one place, edit fast inside the app, or let Jarvis create notes from chat."
      actionLabel="New note"
      onActionPress={openCreateModal}
      stats={[
        { label: "Total notes", value: String(notes.length) },
        { label: "Tagged notes", value: String(taggedNotes) },
        {
          label: "Latest update",
          value: latestNote ? formatDate(latestNote.updated_at).split(",")[0] : "None yet",
        },
      ]}
      error={error}
    >
      <View style={styles.heroHintRow}>
        <View style={styles.heroHintChip}>
          <Ionicons name="pencil-outline" size={14} color={colors.accentStrong} />
          <Text style={styles.heroHintText}>Tap to edit</Text>
        </View>
        <View style={styles.heroHintChip}>
          <Ionicons name="trash-outline" size={14} color={colors.accentStrong} />
          <Text style={styles.heroHintText}>Long press to delete</Text>
        </View>
      </View>
    </ModuleHero>
  );

  if (loading && notes.length === 0) {
    return (
      <View style={styles.center}>
        <ActivityIndicator size="large" color={colors.accentStrong} />
      </View>
    );
  }

  return (
    <AppScreen>
      <FlatList
        data={notes}
        keyExtractor={(item) => item.id}
        keyboardShouldPersistTaps="handled"
        contentContainerStyle={styles.list}
        refreshControl={
          <RefreshControl
            refreshing={loading}
            onRefresh={() => refresh()}
            tintColor={colors.accentStrong}
          />
        }
        ListHeaderComponent={renderHeader}
        ListEmptyComponent={
          <EmptyState
            title="No notes yet."
            text="Start one here or ask Jarvis in chat to create a structured note from your next idea."
          />
        }
        renderItem={({ item }) => (
          <View style={styles.card}>
            <TouchableOpacity onPress={() => openEditModal(item)} onLongPress={() => handleDelete(item)}>
            <View style={styles.cardHeader}>
              <View style={styles.cardTitleWrap}>
                <Text style={styles.title}>{item.title}</Text>
                <Text style={styles.dateLabel}>Updated {formatDate(item.updated_at)}</Text>
              </View>
              <View style={styles.cardAction}>
                <Ionicons name="create-outline" size={16} color={colors.textSoft} />
              </View>
            </View>

            <Text style={styles.content}>{item.content}</Text>

            {item.tags.length > 0 ? (
              <View style={styles.tags}>
                {item.tags.map((tag) => (
                  <View key={tag} style={styles.tag}>
                    <Text style={styles.tagText}>{tag}</Text>
                  </View>
                ))}
              </View>
            ) : null}
            </TouchableOpacity>

            <TouchableOpacity style={styles.knowledgeButton} onPress={() => handleAddToKnowledge(item)}>
              <Ionicons name="library-outline" size={14} color={colors.accentStrong} />
              <Text style={styles.knowledgeButtonText}>Add to Knowledge</Text>
            </TouchableOpacity>
          </View>
        )}
      />

      <Modal animationType="slide" transparent visible={isModalVisible} onRequestClose={closeModal}>
        <KeyboardAvoidingView
          style={styles.modalOverlay}
          behavior={Platform.OS === "ios" ? "padding" : undefined}
        >
          <ModalSheet
            footer={
              <>
                <PrimaryButton variant="light" style={styles.secondaryButton} onPress={closeModal}>
                  Cancel
                </PrimaryButton>
                <PrimaryButton
                  style={[styles.primaryButton, isSaving && styles.disabledButton]}
                  onPress={handleSave}
                  disabled={isSaving}
                >
                  {isSaving ? "Saving..." : editingNote ? "Save changes" : "Create note"}
                </PrimaryButton>
              </>
            }
          >
            <ScrollView contentContainerStyle={styles.modalBody} keyboardShouldPersistTaps="handled">
              <Text style={styles.modalEyebrow}>{editingNote ? "Edit note" : "Create note"}</Text>
              <Text style={styles.modalTitle}>
                {editingNote ? "Refine the note and keep context clean." : "Capture the thought while it is still sharp."}
              </Text>

              <Text style={styles.inputLabel}>Title</Text>
              <TextField
                style={styles.input}
                value={draft.title}
                onChangeText={(title) => setDraft((current) => ({ ...current, title }))}
                placeholder="Sprint planning"
                placeholderTextColor={colors.textSoft}
              />

              <Text style={styles.inputLabel}>Content</Text>
              <TextField
                style={[styles.input, styles.contentInput]}
                value={draft.content}
                onChangeText={(content) => setDraft((current) => ({ ...current, content }))}
                placeholder="Write the note details here"
                placeholderTextColor={colors.textSoft}
                multiline
                textAlignVertical="top"
              />

              <Text style={styles.inputLabel}>Tags</Text>
              <TextField
                style={styles.input}
                value={draft.tags}
                onChangeText={(tags) => setDraft((current) => ({ ...current, tags }))}
                placeholder="work, planning, urgent"
                placeholderTextColor={colors.textSoft}
              />
            </ScrollView>
          </ModalSheet>
        </KeyboardAvoidingView>
      </Modal>
    </AppScreen>
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
    backgroundColor: "rgba(255, 255, 255, 0.55)",
    paddingHorizontal: 12,
    paddingVertical: 9,
    marginRight: 8,
    marginBottom: 8,
  },
  heroHintText: {
    color: colors.ink,
    fontSize: 12,
    fontWeight: "700",
    marginLeft: 8,
  },
  card: {
    backgroundColor: colors.surface,
    borderRadius: radii.md,
    padding: spacing.lg,
    marginBottom: 14,
    borderWidth: 1,
    borderColor: colors.border,
    ...shadows.soft,
  },
  cardHeader: {
    flexDirection: "row",
    alignItems: "flex-start",
    justifyContent: "space-between",
    marginBottom: 10,
  },
  cardTitleWrap: {
    flex: 1,
    paddingRight: spacing.md,
  },
  cardAction: {
    width: 34,
    height: 34,
    borderRadius: 12,
    alignItems: "center",
    justifyContent: "center",
    backgroundColor: colors.surfaceMuted,
  },
  title: {
    fontSize: 18,
    lineHeight: 24,
    fontWeight: "800",
    color: colors.text,
    marginBottom: 4,
  },
  dateLabel: {
    fontSize: 12,
    color: colors.textSoft,
    fontWeight: "600",
  },
  content: {
    fontSize: 14,
    lineHeight: 22,
    color: colors.textMuted,
  },
  tags: {
    flexDirection: "row",
    flexWrap: "wrap",
    marginTop: spacing.md,
  },
  tag: {
    backgroundColor: colors.accentSoft,
    borderRadius: radii.pill,
    paddingHorizontal: 12,
    paddingVertical: 6,
    marginRight: 8,
    marginBottom: 8,
  },
  tagText: {
    color: colors.accentStrong,
    fontSize: 12,
    fontWeight: "700",
  },
  modalOverlay: {
    flex: 1,
    justifyContent: "flex-end",
    backgroundColor: colors.overlay,
  },
  modalBody: {
    paddingBottom: 0,
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
    marginBottom: spacing.md,
  },
  contentInput: {
    minHeight: 160,
  },
  secondaryButton: {
    flex: 1,
    marginRight: 12,
  },
  primaryButton: {
    flex: 1.3,
  },
  disabledButton: {
    opacity: 0.6,
  },
  knowledgeButton: {
    marginTop: spacing.sm,
    flexDirection: "row",
    alignItems: "center",
    alignSelf: "flex-start",
    borderRadius: radii.pill,
    backgroundColor: colors.accentSoft,
    paddingHorizontal: 12,
    paddingVertical: 8,
  },
  knowledgeButtonText: {
    color: colors.accentStrong,
    fontSize: 12,
    fontWeight: "800",
    marginLeft: 8,
  },
});
