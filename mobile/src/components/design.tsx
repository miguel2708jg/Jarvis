import React from "react";
import {
  StyleProp,
  StyleSheet,
  Text,
  TextInput,
  TextInputProps,
  TextStyle,
  TouchableOpacity,
  TouchableOpacityProps,
  View,
  ViewStyle,
} from "react-native";
import { Ionicons } from "@expo/vector-icons";

import { colors, radii, shadows, spacing, typography } from "../theme/tokens";

type IconName = React.ComponentProps<typeof Ionicons>["name"];

export function Card({
  children,
  style,
  compact,
  tone = "plain",
}: {
  children: React.ReactNode;
  style?: StyleProp<ViewStyle>;
  compact?: boolean;
  tone?: "plain" | "muted" | "primary" | "warning";
}) {
  return <View style={[styles.card, compact && styles.cardCompact, styles[`card_${tone}`], style]}>{children}</View>;
}

export function MetricCard({ label, value }: { label: string; value: string }) {
  return (
    <View style={styles.metricCard}>
      <Text style={styles.metricValue}>{value}</Text>
      <Text style={styles.metricLabel}>{label}</Text>
    </View>
  );
}

export function Chip({
  label,
  icon,
  selected,
  tone = "primary",
  onPress,
  style,
}: {
  label: string;
  icon?: IconName;
  selected?: boolean;
  tone?: "primary" | "warning" | "success" | "danger" | "neutral";
  onPress?: () => void;
  style?: StyleProp<ViewStyle>;
}) {
  const content = (
    <>
      {icon ? (
        <Ionicons
          name={icon}
          size={14}
          color={selected ? colors.white : toneColor[tone]}
          style={styles.chipIcon}
        />
      ) : null}
      <Text style={[styles.chipText, { color: selected ? colors.white : toneColor[tone] }]}>{label}</Text>
    </>
  );

  const chipStyle = [styles.chip, selected && styles.chipSelected, style];
  if (onPress) {
    return (
      <TouchableOpacity style={chipStyle} onPress={onPress}>
        {content}
      </TouchableOpacity>
    );
  }
  return <View style={chipStyle}>{content}</View>;
}

export function SegmentedControl<T extends string>({
  value,
  options,
  onChange,
}: {
  value: T;
  options: { label: string; value: T }[];
  onChange: (value: T) => void;
}) {
  return (
    <View style={styles.segmented}>
      {options.map((option) => (
        <TouchableOpacity
          key={option.value}
          style={[styles.segmentItem, value === option.value && styles.segmentItemActive]}
          onPress={() => onChange(option.value)}
        >
          <Text style={[styles.segmentText, value === option.value && styles.segmentTextActive]}>
            {option.label}
          </Text>
        </TouchableOpacity>
      ))}
    </View>
  );
}

export function PrimaryButton({
  children,
  variant = "dark",
  icon,
  style,
  textStyle,
  disabled,
  ...props
}: TouchableOpacityProps & {
  children: React.ReactNode;
  variant?: "dark" | "light" | "warning";
  icon?: IconName;
  textStyle?: StyleProp<TextStyle>;
}) {
  return (
    <TouchableOpacity
      {...props}
      disabled={disabled}
      style={[styles.button, styles[`button_${variant}`], disabled && styles.disabled, style]}
    >
      {icon ? (
        <Ionicons
          name={icon}
          size={16}
          color={variant === "light" ? colors.text : colors.white}
          style={styles.buttonIcon}
        />
      ) : null}
      <Text style={[styles.buttonText, variant === "light" && styles.buttonTextLight, textStyle]}>
        {children}
      </Text>
    </TouchableOpacity>
  );
}

export function IconButton({
  icon,
  selected,
  tone = "light",
  ...props
}: TouchableOpacityProps & { icon: IconName; selected?: boolean; tone?: "light" | "dark" | "warning" }) {
  return (
    <TouchableOpacity
      {...props}
      style={[styles.iconButton, styles[`iconButton_${tone}`], selected && styles.iconButtonSelected, props.style]}
    >
      <Ionicons
        name={icon}
        size={18}
        color={selected || tone === "dark" ? colors.white : colors.text}
      />
    </TouchableOpacity>
  );
}

export function TextField(props: TextInputProps) {
  return (
    <TextInput
      {...props}
      placeholderTextColor={props.placeholderTextColor ?? colors.textSoft}
      style={[styles.input, props.multiline && styles.inputMultiline, props.style]}
    />
  );
}

export function EmptyState({ title, text }: { title: string; text: string }) {
  return (
    <Card style={styles.empty}>
      <Text style={styles.emptyTitle}>{title}</Text>
      <Text style={styles.emptyText}>{text}</Text>
    </Card>
  );
}

export function ErrorBanner({ error }: { error?: string | null }) {
  if (!error) {
    return null;
  }
  return <Text style={styles.errorBanner}>{error}</Text>;
}

export function SectionTitle({ eyebrow, title }: { eyebrow?: string; title: string }) {
  return (
    <View style={styles.sectionTitleWrap}>
      {eyebrow ? <Text style={styles.eyebrow}>{eyebrow}</Text> : null}
      <Text style={styles.sectionTitle}>{title}</Text>
    </View>
  );
}

export function ModalSheet({
  children,
  footer,
  style,
}: {
  children: React.ReactNode;
  footer?: React.ReactNode;
  style?: StyleProp<ViewStyle>;
}) {
  return (
    <View style={[styles.modalCard, style]}>
      <View style={styles.modalHandle} />
      <View style={styles.modalContent}>{children}</View>
      {footer ? <View style={styles.modalFooter}>{footer}</View> : null}
    </View>
  );
}

const toneColor = {
  primary: colors.primaryStrong,
  warning: colors.warningStrong,
  success: colors.success,
  danger: colors.danger,
  neutral: colors.textMuted,
};

const styles = StyleSheet.create({
  card: {
    backgroundColor: colors.surface,
    borderRadius: radii.md,
    borderWidth: 1,
    borderColor: colors.border,
    padding: spacing.lg,
    ...shadows.soft,
  },
  cardCompact: {
    padding: spacing.md,
  },
  card_plain: {},
  card_muted: {
    backgroundColor: colors.surfaceMuted,
  },
  card_primary: {
    backgroundColor: colors.primarySoft,
    borderColor: "rgba(47, 125, 106, 0.16)",
  },
  card_warning: {
    backgroundColor: colors.warningSoft,
    borderColor: "rgba(179, 119, 18, 0.18)",
  },
  metricCard: {
    flex: 1,
    minWidth: 92,
    backgroundColor: colors.surface,
    borderRadius: radii.md,
    padding: spacing.md,
    borderWidth: 1,
    borderColor: "rgba(255, 255, 255, 0.7)",
  },
  metricValue: {
    color: colors.ink,
    fontSize: 21,
    fontWeight: "800",
    marginBottom: 2,
  },
  metricLabel: {
    color: colors.textMuted,
    fontSize: 12,
    lineHeight: 16,
    fontWeight: "700",
  },
  chip: {
    minHeight: 34,
    flexDirection: "row",
    alignItems: "center",
    alignSelf: "flex-start",
    borderRadius: radii.pill,
    backgroundColor: colors.surfaceMuted,
    borderWidth: 1,
    borderColor: colors.border,
    paddingHorizontal: 12,
    paddingVertical: 8,
  },
  chipSelected: {
    backgroundColor: colors.ink,
    borderColor: colors.ink,
  },
  chipIcon: {
    marginRight: 7,
  },
  chipText: {
    fontSize: 12,
    fontWeight: "800",
  },
  segmented: {
    flexDirection: "row",
    padding: 4,
    borderRadius: radii.pill,
    backgroundColor: "rgba(255, 255, 255, 0.42)",
    borderWidth: 1,
    borderColor: "rgba(255, 255, 255, 0.58)",
  },
  segmentItem: {
    flex: 1,
    alignItems: "center",
    borderRadius: radii.pill,
    paddingVertical: 9,
    paddingHorizontal: 10,
  },
  segmentItemActive: {
    backgroundColor: colors.ink,
  },
  segmentText: {
    color: colors.ink,
    fontSize: 12,
    fontWeight: "800",
    textTransform: "capitalize",
  },
  segmentTextActive: {
    color: colors.white,
  },
  button: {
    minHeight: 46,
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    borderRadius: radii.pill,
    paddingHorizontal: 18,
    paddingVertical: 12,
  },
  button_dark: {
    backgroundColor: colors.ink,
  },
  button_light: {
    backgroundColor: colors.surfaceMuted,
    borderWidth: 1,
    borderColor: colors.border,
  },
  button_warning: {
    backgroundColor: colors.warning,
  },
  buttonText: {
    color: colors.white,
    fontSize: 14,
    fontWeight: "800",
  },
  buttonTextLight: {
    color: colors.text,
  },
  buttonIcon: {
    marginRight: 8,
  },
  disabled: {
    opacity: 0.58,
  },
  iconButton: {
    width: 40,
    height: 40,
    borderRadius: 20,
    alignItems: "center",
    justifyContent: "center",
  },
  iconButton_light: {
    backgroundColor: colors.surfaceMuted,
    borderWidth: 1,
    borderColor: colors.border,
  },
  iconButton_dark: {
    backgroundColor: colors.ink,
  },
  iconButton_warning: {
    backgroundColor: colors.warning,
  },
  iconButtonSelected: {
    backgroundColor: colors.ink,
  },
  input: {
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: radii.md,
    paddingHorizontal: 15,
    paddingVertical: 13,
    fontSize: 15,
    lineHeight: 21,
    color: colors.text,
    backgroundColor: colors.surfaceMuted,
  },
  inputMultiline: {
    textAlignVertical: "top",
  },
  empty: {
    padding: spacing.xl,
  },
  emptyTitle: {
    color: colors.text,
    fontSize: 22,
    lineHeight: 27,
    fontWeight: "800",
    marginBottom: spacing.sm,
  },
  emptyText: {
    color: colors.textMuted,
    ...typography.body,
  },
  errorBanner: {
    marginTop: spacing.md,
    paddingHorizontal: 12,
    paddingVertical: 10,
    borderRadius: radii.sm,
    backgroundColor: colors.dangerSoft,
    color: colors.danger,
    fontSize: 13,
    lineHeight: 18,
    fontWeight: "700",
  },
  sectionTitleWrap: {
    marginBottom: spacing.sm,
  },
  eyebrow: {
    color: colors.primaryStrong,
    ...typography.eyebrow,
    textTransform: "uppercase",
    marginBottom: spacing.xs,
  },
  sectionTitle: {
    color: colors.text,
    ...typography.sectionTitle,
  },
  modalCard: {
    backgroundColor: colors.surface,
    borderTopLeftRadius: radii.xl,
    borderTopRightRadius: radii.xl,
    maxHeight: "92%",
  },
  modalHandle: {
    width: 52,
    height: 5,
    borderRadius: radii.pill,
    backgroundColor: colors.border,
    alignSelf: "center",
    marginTop: 10,
  },
  modalContent: {
    padding: spacing.xl,
    paddingBottom: spacing.md,
  },
  modalFooter: {
    flexDirection: "row",
    paddingHorizontal: spacing.xl,
    paddingBottom: 30,
  },
});
