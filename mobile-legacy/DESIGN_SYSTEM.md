# Jarvis Mobile Design System

## Direction
Jarvis mobile uses a calm productivity dashboard style inspired by compact learning-app interfaces: cream/mint backgrounds, white cards, teal hierarchy, yellow action accents, and a black floating tab bar.

## Tokens
- Backgrounds: `colors.background`, `colors.backgroundMuted`, `colors.surface`, `colors.surfaceMuted`.
- Primary: `colors.primary`, `colors.primaryStrong`, `colors.primarySoft`.
- Action accent: `colors.warning`, `colors.warningStrong`, `colors.warningSoft`.
- Text: `colors.text`, `colors.textMuted`, `colors.textSoft`, `colors.ink`.
- Status: `colors.success`, `colors.danger` and their soft variants.
- Shape: use `radii.md` for cards and inputs, `radii.xl` for hero surfaces, `radii.pill` for chips and major actions.

## Components
- Use `AppScreen` for mobile screens so the mint background and safe area stay consistent.
- Use `ModuleHero` for module headers with stats and one primary action.
- Use `Card`, `MetricCard`, `Chip`, `SegmentedControl`, `PrimaryButton`, `IconButton`, `TextField`, `EmptyState`, `ErrorBanner`, and `ModalSheet` for repeated UI patterns.
- Keep cards compact and scannable. Prefer icon-led chips and buttons for operations.

## Layout Rules
- Screens use `spacing.md` horizontal padding and `paddingBottom: 128` when behind the floating tab bar.
- Keep repeated list items on white cards with one clear title, muted metadata, and a small status/action affordance.
- Primary creation or send actions use the yellow accent. System navigation uses the black tab bar.
- Avoid adding new color literals in screens unless a data status requires a one-off semantic color.
