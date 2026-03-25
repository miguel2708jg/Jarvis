import React from "react";
import { NavigationContainer } from "@react-navigation/native";
import { createBottomTabNavigator } from "@react-navigation/bottom-tabs";
import { Ionicons } from "@expo/vector-icons";

import ChatScreen from "../screens/ChatScreen";
import NotesScreen from "../screens/NotesScreen";
import TodosScreen from "../screens/TodosScreen";
import CalendarScreen from "../screens/CalendarScreen";
import EmailScreen from "../screens/EmailScreen";

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
  { name: "Todos", component: TodosScreen, icon: "checkmark-circle-outline", activeIcon: "checkmark-circle" },
  { name: "Calendar", component: CalendarScreen, icon: "calendar-outline", activeIcon: "calendar" },
  { name: "Email", component: EmailScreen, icon: "mail-outline", activeIcon: "mail" },
];

export default function AppNavigator() {
  return (
    <NavigationContainer>
      <Tab.Navigator
        screenOptions={({ route }) => ({
          tabBarIcon: ({ focused, color, size }) => {
            const tab = TABS.find((t) => t.name === route.name)!;
            return <Ionicons name={focused ? tab.activeIcon : tab.icon} size={size} color={color} />;
          },
          tabBarActiveTintColor: "#007AFF",
          tabBarInactiveTintColor: "#8E8E93",
          tabBarStyle: { borderTopColor: "#C6C6C8" },
          headerStyle: { backgroundColor: "#FFFFFF" },
          headerTitleStyle: { fontWeight: "600" },
        })}
      >
        {TABS.map((tab) => (
          <Tab.Screen key={tab.name} name={tab.name} component={tab.component} />
        ))}
      </Tab.Navigator>
    </NavigationContainer>
  );
}
