import {
  Activity,
  BarChart3,
  BriefcaseBusiness,
  Compass,
  MessageCircleHeart,
  MessagesSquare,
  Sparkles,
  Timer,
  WandSparkles,
  type LucideIcon,
} from "lucide-react";
import type { PersonalityId } from "./types";

export interface PersonalityOption {
  id: PersonalityId;
  name: string;
  command: string;
  shortRole: string;
  Icon: LucideIcon;
}

export const PERSONALITIES: PersonalityOption[] = [
  { id: "mentor", name: "Mentor", command: "/mentor", shortRole: "Decisiones profundas", Icon: Compass },
  { id: "ceo", name: "CEO", command: "/ceo", shortRole: "Ejecucion", Icon: BriefcaseBusiness },
  { id: "coach", name: "Coach", command: "/coach", shortRole: "Claridad", Icon: Activity },
  { id: "amigo", name: "Amigo", command: "/amigo", shortRole: "Casual", Icon: MessageCircleHeart },
  { id: "rizz", name: "Rizz", command: "/rizz", shortRole: "Carisma", Icon: Sparkles },
  { id: "focus", name: "Focus", command: "/focus", shortRole: "Accion", Icon: Timer },
  { id: "analista", name: "Analista", command: "/analista", shortRole: "Datos", Icon: BarChart3 },
  { id: "creativo", name: "Creativo", command: "/creativo", shortRole: "Ideas", Icon: WandSparkles },
  { id: "social_copilot", name: "Social", command: "/social", shortRole: "Mensajes", Icon: MessagesSquare },
];

export const COMMAND_TO_PERSONALITY_ID = PERSONALITIES.reduce<Record<string, PersonalityId>>((acc, personality) => {
  acc[personality.command] = personality.id;
  return acc;
}, {});

export function getPersonality(id: PersonalityId | null): PersonalityOption | null {
  if (!id) return null;
  return PERSONALITIES.find((personality) => personality.id === id) ?? null;
}
