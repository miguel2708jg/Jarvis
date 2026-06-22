/**
 * Orbit Mobile Design System Tokens
 * Mobile-native productivity + AI assistant visual language.
 */

export const designTokens = {
  layout: {
    mobileMax: '430px',
    horizontalPadding: '16px',
    sectionGapMin: '14px',
    sectionGapMax: '18px',
  },

  colors: {
    background: '#09090b',
    backgroundAlt: '#111827',
    surface: '#18181b',
    surfaceSoft: '#111827',

    ink: '#ffffff',
    text: '#ffffff',
    textMuted: '#a1a1aa',
    textSoft: '#71717a',

    primary: {
      main: '#7c3aed',
      strong: '#8b5cf6',
      soft: 'rgba(124, 58, 237, 0.16)',
    },

    teal: {
      main: '#2563eb',
      strong: '#3b82f6',
      soft: 'rgba(37, 99, 235, 0.16)',
    },

    accent: '#2563eb',
    success: '#10b981',
    danger: '#ef4444',
    dangerSoft: 'rgba(239, 68, 68, 0.14)',
    warning: '#f59e0b',
    info: '#3b82f6',
    border: '#27272a',
    borderSecondary: '#3f3f46',
    tabbar: 'rgba(9, 9, 11, 0.92)',
  },

  typography: {
    fontSize: {
      eyebrow: '11px',
      metadata: '12px',
      body: '14px',
      bodyLarge: '16px',
      h2: '20px',
      h1: '30px',
    },
    fontWeight: {
      normal: 400,
      semibold: 650,
      bold: 800,
      extrabold: 850,
      black: 900,
    },
    lineHeight: {
      tight: 1.08,
      snug: 1.2,
      normal: 1.5,
    },
    letterSpacing: {
      normal: 0,
      wide: '0.7px',
      wider: '1.4px',
    },
  },

  spacing: {
    xs: '2px',
    sm: '4px',
    md: '6px',
    lg: '8px',
    xl: '10px',
    '2xl': '12px',
    '3xl': '14px',
    '4xl': '16px',
    '5xl': '18px',
    '6xl': '20px',
    '7xl': '22px',
    '8xl': '24px',
    '12xl': '32px',
  },

  borderRadius: {
    sm: '12px',
    md: '14px',
    lg: '20px',
    xl: '24px',
    pill: '999px',
  },

  shadows: {
    soft: '0 0 20px rgba(124, 58, 237, 0.15)',
    strong: '0 0 30px rgba(124, 58, 237, 0.25)',
  },

  zIndex: {
    hide: -1,
    auto: 'auto',
    base: 0,
    dropdown: 10,
    sticky: 20,
    tabbar: 30,
    modal: 40,
    popover: 50,
  },

  breakpoints: {
    xs: 340,
    mobile: 430,
  },
} as const;

/**
 * CSS Custom Properties Map
 * Maps design tokens to CSS variable names.
 */
export const cssVariableMap = {
  '--mobile-max': designTokens.layout.mobileMax,

  '--background': designTokens.colors.background,
  '--background-alt': designTokens.colors.backgroundAlt,
  '--surface': designTokens.colors.surface,
  '--surface-soft': designTokens.colors.surfaceSoft,
  '--ink': designTokens.colors.ink,
  '--text': designTokens.colors.text,
  '--text-muted': designTokens.colors.textMuted,
  '--text-soft': designTokens.colors.textSoft,
  '--primary': designTokens.colors.primary.main,
  '--primary-strong': designTokens.colors.primary.strong,
  '--primary-soft': designTokens.colors.primary.soft,
  '--teal': designTokens.colors.teal.main,
  '--teal-strong': designTokens.colors.teal.strong,
  '--teal-soft': designTokens.colors.teal.soft,
  '--accent': designTokens.colors.accent,
  '--success': designTokens.colors.success,
  '--danger': designTokens.colors.danger,
  '--warning': designTokens.colors.warning,
  '--info': designTokens.colors.info,
  '--border': designTokens.colors.border,
  '--border-secondary': designTokens.colors.borderSecondary,
  '--tabbar': designTokens.colors.tabbar,
  '--orbit-gradient': 'linear-gradient(135deg, #7c3aed, #2563eb)',

  '--radius-sm': designTokens.borderRadius.sm,
  '--radius-md': designTokens.borderRadius.md,
  '--radius-lg': designTokens.borderRadius.lg,
  '--radius-xl': designTokens.borderRadius.xl,
  '--radius-pill': designTokens.borderRadius.pill,
  '--shadow-soft': designTokens.shadows.soft,
  '--shadow-strong': designTokens.shadows.strong,

  '--background-muted': designTokens.colors.backgroundAlt,
  '--surface-muted': designTokens.colors.surfaceSoft,
  '--secondary': designTokens.colors.tabbar,
  '--accent-strong': designTokens.colors.primary.strong,
  '--accent-soft': designTokens.colors.primary.soft,
  '--success-soft': 'rgba(16, 185, 129, 0.14)',
  '--danger-soft': designTokens.colors.dangerSoft,
  '--warning-soft': 'rgba(245, 158, 11, 0.16)',
  '--amber-soft': 'rgba(245, 158, 11, 0.16)',
  '--sky-soft': designTokens.colors.teal.soft,
  '--lavender': designTokens.colors.primary.soft,
  '--orange': designTokens.colors.accent,
  '--pink': designTokens.colors.primary.main,
  '--shadow': designTokens.shadows.strong,
  '--radius-full': designTokens.borderRadius.pill,
} as const;

export type DesignTokens = typeof designTokens;
export type CSSVariableMap = typeof cssVariableMap;
