import "react-native-get-random-values";
import { Tabs } from "expo-router";
import { StyleSheet, View } from "react-native";

export default function Layout() {
  return (
    <Tabs
      screenOptions={{
        tabBarIcon: ({ color }) => <View style={[styles.tabMark, { backgroundColor: color }]} />,
      }}
    >
      <Tabs.Screen name="wallet" options={{ title: "Wallet" }} />
      <Tabs.Screen name="index" options={{ title: "Run" }} />
      <Tabs.Screen name="analytics" options={{ title: "Analytics" }} />
    </Tabs>
  );
}

const styles = StyleSheet.create({
  tabMark: { borderRadius: 2, height: 3, width: 18 },
});
