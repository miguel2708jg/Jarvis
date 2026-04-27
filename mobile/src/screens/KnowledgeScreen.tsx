import React, { useCallback, useMemo, useState } from "react";
import {
  ActivityIndicator,
  Alert,
  FlatList,
  Modal,
  RefreshControl,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  TouchableOpacity,
  View,
} from "react-native";
import * as DocumentPicker from "expo-document-picker";
import { useFocusEffect } from "@react-navigation/native";
import { SafeAreaView } from "react-native-safe-area-context";
import { Ionicons } from "@expo/vector-icons";

import type { KnowledgePage, KnowledgePageDetail } from "../api/types";
import ModuleHero from "../components/ModuleHero";
import ScreenBackground from "../components/ScreenBackground";
import { useKnowledge } from "../hooks/useJarvisApi";
import { colors, radii, shadows, spacing } from "../theme/tokens";

const TYPE_OPTIONS = ["all", "overview", "entity", "concept", "source", "analysis"] as const;

function formatDate(value: string): string {
  if (!value) {
    return "Unknown";
  }
  try {
    return new Date(value).toLocaleString(undefined, {
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  } catch {
    return value;
  }
}

export default function KnowledgeScreen() {
  const { status, pages, sources, loading, error, refresh, getPage, ingestNote, uploadFile, runLint } = useKnowledge();
  const [selectedType, setSelectedType] = useState<(typeof TYPE_OPTIONS)[number]>("all");
  const [query, setQuery] = useState("");
  const [noteId, setNoteId] = useState("");
  const [detail, setDetail] = useState<KnowledgePageDetail | null>(null);
  const [detailOpen, setDetailOpen] = useState(false);

  const refreshWithFilters = useCallback(() => {
    return refresh({
      type: selectedType === "all" ? undefined : selectedType,
      q: query.trim() || undefined,
    });
  }, [query, refresh, selectedType]);

  useFocusEffect(
    useCallback(() => {
      refreshWithFilters();
    }, [refreshWithFilters])
  );

  const openDetail = useCallback(async (path: string) => {
    const page = await getPage(path);
    if (!page) {
      return;
    }
    setDetail(page);
    setDetailOpen(true);
  }, [getPage]);

  const handleIngestNote = useCallback(async () => {
    const trimmed = noteId.trim();
    if (!trimmed) {
      Alert.alert("Missing note ID", "Enter a note ID before ingesting.");
      return;
    }
    const result = await ingestNote(trimmed);
    if (!result) {
      Alert.alert("Ingest failed", "Jarvis could not ingest that note.");
      return;
    }
    Alert.alert("Ingest complete", `${result.touched_pages.length} page(s) updated.`);
    setNoteId("");
  }, [ingestNote, noteId]);

  const handleUploadFile = useCallback(async () => {
    const picked = await DocumentPicker.getDocumentAsync({
      copyToCacheDirectory: true,
      type: ["text/plain", "text/markdown", "application/pdf"],
      multiple: false,
    });
    if (picked.canceled || picked.assets.length === 0) {
      return;
    }
    const asset = picked.assets[0];
    const result = await uploadFile({
      uri: asset.uri,
      name: asset.name ?? "upload.txt",
      type: asset.mimeType ?? "application/octet-stream",
    });
    if (!result) {
      Alert.alert("Upload failed", "Jarvis could not ingest the selected file.");
      return;
    }
    Alert.alert("Upload complete", `${result.touched_pages.length} page(s) updated.`);
  }, [uploadFile]);

  const handleLint = useCallback(async () => {
    const result = await runLint();
    if (!result) {
      Alert.alert("Lint failed", "Jarvis could not lint the knowledge vault.");
      return;
    }
    Alert.alert("Lint complete", `${result.touched_pages.length} page(s) updated.`);
  }, [runLint]);

  const heroStats = useMemo(
    () => [
      { label: "Pages", value: String(status?.page_count ?? 0) },
      { label: "Sources", value: String(status?.source_count ?? 0) },
      { label: "Last op", value: status?.last_log_entry ? "Available" : "None" },
    ],
    [status]
  );

  const renderPage = ({ item }: { item: KnowledgePage }) => (
    <TouchableOpacity style={styles.pageCard} onPress={() => openDetail(item.path)}>
      <View style={styles.pageHeader}>
        <Text style={styles.pageType}>{item.type.toUpperCase()}</Text>
        <Text style={styles.pageDate}>{formatDate(item.updated_at)}</Text>
      </View>
      <Text style={styles.pageTitle}>{item.title}</Text>
      <Text style={styles.pagePath}>{item.path}</Text>
      {item.summary ? <Text style={styles.pageSummary}>{item.summary}</Text> : null}
      {item.tags.length > 0 ? (
        <View style={styles.tagRow}>
          {item.tags.slice(0, 4).map((tag) => (
            <View key={tag} style={styles.tagChip}>
              <Text style={styles.tagText}>{tag}</Text>
            </View>
          ))}
        </View>
      ) : null}
    </TouchableOpacity>
  );

  return (
    <SafeAreaView style={styles.container} edges={["top"]}>
      <ScreenBackground />
      <FlatList
        data={pages}
        keyExtractor={(item) => item.path}
        renderItem={renderPage}
        contentContainerStyle={styles.list}
        refreshControl={
          <RefreshControl
            refreshing={loading}
            onRefresh={refreshWithFilters}
            tintColor={colors.accentStrong}
          />
        }
        ListHeaderComponent={
          <View>
            <ModuleHero
              eyebrow="Knowledge Vault"
              title="Obsidian-style wiki with explicit operations."
              subtitle="Ingest notes/files, run lint maintenance, and navigate linked knowledge pages."
              actionLabel="Run lint"
              onActionPress={handleLint}
              stats={heroStats}
              error={error}
            />

            <View style={styles.actionsCard}>
              <Text style={styles.sectionTitle}>Operations</Text>
              <TextInput
                value={noteId}
                onChangeText={setNoteId}
                placeholder="Note ID to ingest"
                placeholderTextColor={colors.textSoft}
                style={styles.input}
              />
              <View style={styles.actionRow}>
                <TouchableOpacity style={styles.secondaryButton} onPress={handleIngestNote}>
                  <Ionicons name="archive-outline" size={16} color={colors.text} />
                  <Text style={styles.secondaryButtonText}>Ingest note</Text>
                </TouchableOpacity>
                <TouchableOpacity style={styles.secondaryButton} onPress={handleUploadFile}>
                  <Ionicons name="cloud-upload-outline" size={16} color={colors.text} />
                  <Text style={styles.secondaryButtonText}>Upload file</Text>
                </TouchableOpacity>
              </View>
            </View>

            <View style={styles.filtersCard}>
              <TextInput
                value={query}
                onChangeText={setQuery}
                onSubmitEditing={refreshWithFilters}
                placeholder="Search by title, summary, tags, aliases"
                placeholderTextColor={colors.textSoft}
                style={styles.input}
              />
              <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.typeRow}>
                {TYPE_OPTIONS.map((type) => (
                  <TouchableOpacity
                    key={type}
                    style={[styles.typeChip, selectedType === type && styles.typeChipActive]}
                    onPress={() => {
                      setSelectedType(type);
                      setTimeout(refreshWithFilters, 0);
                    }}
                  >
                    <Text style={[styles.typeChipText, selectedType === type && styles.typeChipTextActive]}>
                      {type}
                    </Text>
                  </TouchableOpacity>
                ))}
              </ScrollView>
            </View>

            <View style={styles.sourcesCard}>
              <Text style={styles.sectionTitle}>Recent sources</Text>
              {sources.slice(0, 6).map((source) => (
                <View key={source.source_id} style={styles.sourceRow}>
                  <Text style={styles.sourceTitle}>{source.title}</Text>
                  <Text style={styles.sourceMeta}>
                    {source.kind} | {formatDate(source.created_at)}
                  </Text>
                </View>
              ))}
            </View>
          </View>
        }
        ListEmptyComponent={
          loading ? (
            <View style={styles.center}>
              <ActivityIndicator size="large" color={colors.accentStrong} />
            </View>
          ) : (
            <View style={styles.emptyCard}>
              <Text style={styles.emptyTitle}>No knowledge pages found.</Text>
              <Text style={styles.emptyText}>Ingest a note or upload a file to compile the first pages.</Text>
            </View>
          )
        }
      />

      <Modal visible={detailOpen} animationType="slide" transparent onRequestClose={() => setDetailOpen(false)}>
        <View style={styles.modalOverlay}>
          <View style={styles.modalCard}>
            <TouchableOpacity style={styles.modalClose} onPress={() => setDetailOpen(false)}>
              <Ionicons name="close" size={20} color={colors.text} />
            </TouchableOpacity>
            {detail ? (
              <ScrollView contentContainerStyle={styles.modalBody}>
                <Text style={styles.modalType}>{detail.type.toUpperCase()}</Text>
                <Text style={styles.modalTitle}>{detail.title}</Text>
                <Text style={styles.modalMeta}>{detail.path}</Text>
                {detail.summary ? <Text style={styles.modalSummary}>{detail.summary}</Text> : null}
                <Text style={styles.modalSection}>Body</Text>
                <Text style={styles.modalBodyText}>{detail.body}</Text>
                {detail.wikilinks.length > 0 ? (
                  <>
                    <Text style={styles.modalSection}>Wikilinks</Text>
                    <View style={styles.tagRow}>
                      {detail.wikilinks.map((link) => (
                        <TouchableOpacity
                          key={link}
                          style={styles.linkChip}
                          onPress={() => openDetail(link)}
                        >
                          <Text style={styles.linkChipText}>{link}</Text>
                        </TouchableOpacity>
                      ))}
                    </View>
                  </>
                ) : null}
              </ScrollView>
            ) : null}
          </View>
        </View>
      </Modal>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.background,
  },
  list: {
    padding: spacing.md,
    paddingBottom: 128,
  },
  actionsCard: {
    backgroundColor: colors.surface,
    borderRadius: radii.lg,
    borderWidth: 1,
    borderColor: colors.border,
    padding: spacing.lg,
    marginBottom: spacing.md,
    ...shadows.soft,
  },
  filtersCard: {
    backgroundColor: colors.surface,
    borderRadius: radii.lg,
    borderWidth: 1,
    borderColor: colors.border,
    padding: spacing.lg,
    marginBottom: spacing.md,
    ...shadows.soft,
  },
  sourcesCard: {
    backgroundColor: colors.surface,
    borderRadius: radii.lg,
    borderWidth: 1,
    borderColor: colors.border,
    padding: spacing.lg,
    marginBottom: spacing.md,
    ...shadows.soft,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: "800",
    color: colors.text,
    marginBottom: spacing.sm,
  },
  input: {
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: radii.md,
    paddingHorizontal: 14,
    paddingVertical: 12,
    backgroundColor: colors.backgroundMuted,
    color: colors.text,
    marginBottom: spacing.sm,
  },
  actionRow: {
    flexDirection: "row",
    gap: 10,
  },
  secondaryButton: {
    flex: 1,
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    borderRadius: radii.md,
    borderWidth: 1,
    borderColor: colors.border,
    backgroundColor: colors.backgroundMuted,
    paddingVertical: 12,
  },
  secondaryButtonText: {
    marginLeft: 8,
    color: colors.text,
    fontWeight: "700",
    fontSize: 14,
  },
  typeRow: {
    paddingVertical: 4,
  },
  typeChip: {
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: radii.pill,
    paddingHorizontal: 12,
    paddingVertical: 8,
    marginRight: 8,
    backgroundColor: colors.backgroundMuted,
  },
  typeChipActive: {
    backgroundColor: colors.ink,
    borderColor: colors.ink,
  },
  typeChipText: {
    color: colors.textMuted,
    fontWeight: "700",
    textTransform: "capitalize",
  },
  typeChipTextActive: {
    color: colors.white,
  },
  sourceRow: {
    paddingVertical: 8,
    borderBottomWidth: 1,
    borderBottomColor: colors.border,
  },
  sourceTitle: {
    color: colors.text,
    fontSize: 14,
    fontWeight: "700",
  },
  sourceMeta: {
    color: colors.textMuted,
    fontSize: 12,
    marginTop: 2,
  },
  pageCard: {
    backgroundColor: colors.surface,
    borderRadius: radii.lg,
    borderWidth: 1,
    borderColor: colors.border,
    padding: spacing.lg,
    marginBottom: spacing.md,
    ...shadows.soft,
  },
  pageHeader: {
    flexDirection: "row",
    justifyContent: "space-between",
    marginBottom: 6,
  },
  pageType: {
    color: colors.accentStrong,
    fontWeight: "800",
    fontSize: 11,
    letterSpacing: 1.1,
  },
  pageDate: {
    color: colors.textSoft,
    fontSize: 12,
    fontWeight: "600",
  },
  pageTitle: {
    color: colors.text,
    fontSize: 18,
    fontWeight: "800",
  },
  pagePath: {
    color: colors.textSoft,
    fontSize: 12,
    marginTop: 2,
  },
  pageSummary: {
    color: colors.textMuted,
    fontSize: 14,
    lineHeight: 21,
    marginTop: 8,
  },
  tagRow: {
    flexDirection: "row",
    flexWrap: "wrap",
    marginTop: 10,
  },
  tagChip: {
    borderRadius: radii.pill,
    backgroundColor: colors.accentSoft,
    paddingHorizontal: 10,
    paddingVertical: 6,
    marginRight: 8,
    marginBottom: 8,
  },
  tagText: {
    color: colors.accentStrong,
    fontSize: 12,
    fontWeight: "700",
  },
  center: {
    paddingVertical: 24,
    alignItems: "center",
  },
  emptyCard: {
    backgroundColor: colors.surface,
    borderRadius: radii.lg,
    borderWidth: 1,
    borderColor: colors.border,
    padding: spacing.lg,
  },
  emptyTitle: {
    color: colors.text,
    fontSize: 20,
    fontWeight: "800",
    marginBottom: spacing.xs,
  },
  emptyText: {
    color: colors.textMuted,
    fontSize: 14,
    lineHeight: 20,
  },
  modalOverlay: {
    flex: 1,
    justifyContent: "flex-end",
    backgroundColor: colors.overlay,
  },
  modalCard: {
    backgroundColor: colors.surface,
    borderTopLeftRadius: 24,
    borderTopRightRadius: 24,
    maxHeight: "90%",
  },
  modalClose: {
    alignSelf: "flex-end",
    marginTop: 10,
    marginRight: 10,
    width: 36,
    height: 36,
    borderRadius: 18,
    alignItems: "center",
    justifyContent: "center",
    backgroundColor: colors.backgroundMuted,
  },
  modalBody: {
    padding: spacing.lg,
    paddingBottom: 30,
  },
  modalType: {
    color: colors.accentStrong,
    fontSize: 11,
    fontWeight: "800",
    letterSpacing: 1.2,
  },
  modalTitle: {
    color: colors.text,
    fontSize: 24,
    fontWeight: "800",
    marginTop: 6,
  },
  modalMeta: {
    color: colors.textSoft,
    fontSize: 12,
    marginTop: 4,
  },
  modalSummary: {
    color: colors.textMuted,
    fontSize: 15,
    lineHeight: 22,
    marginTop: 10,
  },
  modalSection: {
    color: colors.text,
    fontSize: 16,
    fontWeight: "800",
    marginTop: 16,
    marginBottom: 8,
  },
  modalBodyText: {
    color: colors.textMuted,
    fontSize: 14,
    lineHeight: 22,
  },
  linkChip: {
    borderRadius: radii.pill,
    borderWidth: 1,
    borderColor: colors.border,
    backgroundColor: colors.backgroundMuted,
    paddingHorizontal: 10,
    paddingVertical: 6,
    marginRight: 8,
    marginBottom: 8,
  },
  linkChipText: {
    color: colors.text,
    fontWeight: "700",
    fontSize: 12,
  },
});
