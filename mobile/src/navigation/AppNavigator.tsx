import React from "react";
import { StyleSheet, View } from "react-native";
import { NavigationContainer } from "@react-navigation/native";
import { createBottomTabNavigator } from "@react-navigation/bottom-tabs";
import { Ionicons } from "@expo/vector-icons";

import CalendarScreen from "../screens/CalendarScreen";
import ChatScreen from "../screens/ChatScreen";
import EmailScreen from "../screens/EmailScreen";
import KnowledgeScreen from "../screens/KnowledgeScreen";
import NotesScreen from "../screens/NotesScreen";
import TodosScreen from "../screens/TodosScreen";
import { colors, radii, shadows } from "../theme/tokens";

const Tab = createBottomTabNavigator();

type IconName = React.ComponentProps<typeof Ionicons>["name"];

const TABS: {
  name: string;
  component: React.ComponentType<any>;
  icon: IconName;
  activeIcon: IconName;
}[] = [
  { name: "Chat", component: ChatScreen, icon: "chatbubble-outline", activeIcon: "chatbubble" },
  { name: "Notes", component: NotesScreen, icon: "document-text-outline", activeIcon: "document-text" },
  { name: "Knowledge", component: KnowledgeScreen, icon: "library-outline", activeIcon: "library" },
  { name: "ToDo", component: TodosScreen, icon: "checkmark-circle-outline", activeIcon: "checkmark-circle" },
  { name: "Calendar", component: CalendarScreen, icon: "calendar-outline", activeIcon: "calendar" },
  { name: "Email", component: EmailScreen, icon: "mail-outline", activeIcon: "mail" },
];

export default function AppNavigator() {
  return (
    <NavigationContainer>
      <Tab.Navigator
        screenOptions={({ route }) => ({
          headerShown: false,
          sceneContainerStyle: { backgroundColor: colors.background },
          tabBarHideOnKeyboard: true,
          tabBarActiveTintColor: colors.accent,
          tabBarInactiveTintColor: "#8B98AE",
          tabBarLabelStyle: styles.tabBarLabel,
          tabBarStyle: styles.tabBar,
          tabBarItemStyle: styles.tabBarItem,
          tabBarBackground: () => <View style={styles.tabBarBackground} />,
          tabBarIcon: ({ focused, color, size }) => {
            const tab = TABS.find((item) => item.name === route.name)!;
            return <Ionicons name={focused ? tab.activeIcon : tab.icon} size={size} color={color} />;
          },
        })}
      >
        {TABS.map((tab) => (
          <Tab.Screen key={tab.name} name={tab.name} component={tab.component} />
        ))}
      </Tab.Navigator>
    </NavigationContainer>
  );
}

const styles = StyleSheet.create({
  tabBar: {
    position: "absolute",
    left: 16,
    right: 16,
    bottom: 16,
    height: 74,
    borderTopWidth: 0,
    backgroundColor: "transparent",
    elevation: 0,
  },
  tabBarBackground: {
    flex: 1,
    borderRadius: radii.lg,
    backgroundColor: colors.tabBar,
    borderWidth: 1,
    borderColor: "rgba(255, 255, 255, 0.08)",
    ...shadows.card,
  },
  tabBarItem: {
    paddingTop: 8,
  },
  tabBarLabel: {
    fontSize: 11,
    fontWeight: "700",
    marginBottom: 4,
  },
});
