export const colors = {
  background: "#EFF7EF",
  backgroundMuted: "#E3F0E9",
  surface: "#FFFFFF",
  surfaceMuted: "#F7FBF7",
  surfaceStrong: "#D8EADF",
  ink: "#101612",
  inkMuted: "#2E3A33",
  text: "#17201B",
  textMuted: "#69766E",
  textSoft: "#9BA79F",
  border: "#DCE9DF",
  primary: "#4F9B88",
  primaryStrong: "#2F7D6A",
  primarySoft: "#DCEFE8",
  accent: "#5AAE98",
  accentStrong: "#2F7D6A",
  accentSoft: "#E4F4EE",
  warning: "#F2BE3E",
  warningStrong: "#B37712",
  warningSoft: "#FFF1C8",
  amber: "#F2BE3E",
  amberSoft: "#FFF1C8",
  success: "#2D9B68",
  successSoft: "#D8F2E0",
  danger: "#D65A56",
  dangerSoft: "#FBE1DE",
  sky: "#8ECAC4",
  skySoft: "#E1F3F0",
  mint: "#CFE9D8",
  lavender: "#DCEFE8",
  pink: "#F1B8C9",
  orange: "#F4C35D",
  white: "#FFFFFF",
  overlay: "rgba(16, 22, 18, 0.38)",
  shadow: "rgba(53, 83, 67, 0.14)",
  tabBar: "#090C0A",
};

export const spacing = {
  xxs: 4,
  xs: 6,
  sm: 10,
  md: 16,
  lg: 20,
  xl: 24,
  xxl: 32,
};

export const radii = {
  xs: 8,
  sm: 12,
  md: 16,
  lg: 22,
  xl: 28,
  pill: 999,
};

export const typography = {
  eyebrow: {
    fontSize: 11,
    lineHeight: 14,
    fontWeight: "800" as const,
    letterSpacing: 1.2,
  },
  title: {
    fontSize: 26,
    lineHeight: 31,
    fontWeight: "800" as const,
  },
  sectionTitle: {
    fontSize: 19,
    lineHeight: 24,
    fontWeight: "800" as const,
  },
  body: {
    fontSize: 14,
    lineHeight: 21,
    fontWeight: "500" as const,
  },
  label: {
    fontSize: 12,
    lineHeight: 16,
    fontWeight: "800" as const,
  },
};

export const shadows = {
  card: {
    shadowColor: "#355343",
    shadowOpacity: 0.11,
    shadowRadius: 16,
    shadowOffset: { width: 0, height: 8 },
    elevation: 4,
  },
  soft: {
    shadowColor: "#355343",
    shadowOpacity: 0.07,
    shadowRadius: 10,
    shadowOffset: { width: 0, height: 5 },
    elevation: 2,
  },
};
