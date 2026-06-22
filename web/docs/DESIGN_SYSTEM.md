# Orbit Design System v1.0

## Visual Direction

Orbit is a dark, premium personal OS for an AI assistant. The interface should feel minimal, fast, and professional, with the user at the center and tools organized around them.

Visual references:
- Deep dark backgrounds.
- Compact dark cards with subtle borders.
- Purple/blue Orbit identity.
- Soft glow on important surfaces.
- Clear hierarchy and high contrast.
- Mobile-first shell that also works cleanly on desktop.

## Tokens

```css
:root {
  --mobile-max: 430px;
  --background: #09090b;
  --background-alt: #111827;
  --surface: #18181b;
  --surface-soft: #111827;

  --border: #27272a;
  --border-secondary: #3f3f46;

  --text: #ffffff;
  --text-muted: #a1a1aa;
  --text-soft: #71717a;

  --primary: #7c3aed;
  --accent: #2563eb;
  --orbit-gradient: linear-gradient(135deg, #7c3aed, #2563eb);

  --success: #10b981;
  --warning: #f59e0b;
  --danger: #ef4444;
  --info: #3b82f6;

  --radius-sm: 12px;
  --radius-md: 14px;
  --radius-lg: 20px;
  --radius-xl: 24px;
  --radius-pill: 999px;

  --shadow-soft: 0 0 20px rgba(124, 58, 237, 0.15);
  --shadow-strong: 0 0 30px rgba(124, 58, 237, 0.25);
}
```

## Components

### Cards

Cards use `--surface`, `--border`, `20px` radius, `24px` preferred padding on roomy surfaces, and Orbit glow only when the surface needs emphasis.

### Buttons

Primary buttons use the Orbit gradient with white text. Secondary buttons are transparent or `--surface-soft` with a visible border. Ghost buttons do not add a filled background.

### Inputs

Inputs use `--background-alt`, `--border`, white text, and muted placeholders.

### Modals

Modals use dark surfaces, a dimmed backdrop, and a soft blur where supported.

### Navigation

The app keeps its centered mobile-first shell and bottom navigation. Active navigation states use the Orbit purple/blue identity.

## UI Rules

- Do not change data flows or business logic for visual changes.
- Keep the app productivity-focused, not space-themed or game-like.
- Use lucide/Ionicons consistently for actions.
- Keep text readable on all dark surfaces.
- Prefer subtle glow over decorative effects.
