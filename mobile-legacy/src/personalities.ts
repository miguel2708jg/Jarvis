import type { ComponentProps } from "react";
import { Ionicons } from "@expo/vector-icons";

export type PersonalityId =
  | "mentor"
  | "ceo"
  | "coach"
  | "amigo"
  | "rizz"
  | "focus"
  | "analista"
  | "creativo"
  | "social_copilot";

export interface PersonalityOption {
  id: PersonalityId;
  name: string;
  command: string;
  shortRole: string;
  icon: ComponentProps<typeof Ionicons>["name"];
}

export const PERSONALITIES: PersonalityOption[] = [
  {
    id: "mentor",
    name: "Mentor",
    command: "/mentor",
    shortRole: "Decisiones profundas",
    icon: "compass-outline",
  },
  {
    id: "ceo",
    name: "CEO",
    command: "/ceo",
    shortRole: "Ejecucion",
    icon: "briefcase-outline",
  },
  {
    id: "coach",
    name: "Coach",
    command: "/coach",
    shortRole: "Claridad",
    icon: "fitness-outline",
  },
  {
    id: "amigo",
    name: "Amigo",
    command: "/amigo",
    shortRole: "Casual",
    icon: "happy-outline",
  },
  {
    id: "rizz",
    name: "Rizz",
    command: "/rizz",
    shortRole: "Carisma",
    icon: "flash-outline",
  },
  {
    id: "focus",
    name: "Focus",
    command: "/focus",
    shortRole: "Accion",
    icon: "timer-outline",
  },
  {
    id: "analista",
    name: "Analista",
    command: "/analista",
    shortRole: "Datos",
    icon: "analytics-outline",
  },
  {
    id: "creativo",
    name: "Creativo",
    command: "/creativo",
    shortRole: "Ideas",
    icon: "color-wand-outline",
  },
  {
    id: "social_copilot",
    name: "Social",
    command: "/social",
    shortRole: "Mensajes",
    icon: "chatbubbles-outline",
  },
];

export const COMMAND_TO_PERSONALITY_ID = PERSONALITIES.reduce<Record<string, PersonalityId>>(
  (acc, personality) => {
    acc[personality.command] = personality.id;
    return acc;
  },
  {}
);

export function getPersonality(id: PersonalityId | null): PersonalityOption | null {
  if (!id) {
    return null;
  }
  return PERSONALITIES.find((personality) => personality.id === id) ?? null;
}
