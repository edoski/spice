import { useState, useEffect, useCallback } from "react";
import { NavigationContainer } from "@react-navigation/native";
import { createBottomTabNavigator } from "@react-navigation/bottom-tabs";
import { Ionicons } from "@expo/vector-icons";

import { InferenceScreen, type InferenceState } from "./src/screens/InferenceScreen";
import { AnalyticsScreen } from "./src/screens/AnalyticsScreen";
import { requestInference, type Chain, type Horizon } from "./src/inference";
import { loadRuns, saveRuns, createRun, type InferenceRun } from "./src/history";

const Tab = createBottomTabNavigator();

export default function App() {
  const [chain, setChain] = useState<Chain>("ethereum");
  const [horizon, setHorizon] = useState<Horizon>(5);
  const [state, setState] = useState<InferenceState>({ status: "idle" });
  
  const [runs, setRuns] = useState<InferenceRun[]>([]);
  const [storageError, setStorageError] = useState<string | null>(null);

  useEffect(() => {
    loadRuns()
      .then(setRuns)
      .catch((err) => setStorageError(err instanceof Error ? err.message : String(err)));
  }, []);

  const handleRun = useCallback(async () => {
    setState({ status: "loading" });
    try {
      const result = await requestInference({ chain, K: horizon });
      setState({ status: "success", result });
      
      const newRun = createRun({ chain, K: horizon }, result);
      setRuns((prev) => {
        const next = [newRun, ...prev];
        saveRuns(next).catch((err) => setStorageError(err instanceof Error ? err.message : String(err)));
        return next;
      });
    } catch (err) {
      setState({ status: "error", message: err instanceof Error ? err.message : String(err) });
    }
  }, [chain, horizon]);

  const handleRunAgain = useCallback(() => {
    setState({ status: "idle" });
  }, []);

  const handleChainChange = useCallback((c: Chain) => {
    setChain(c);
    setState({ status: "idle" });
  }, []);

  const handleHorizonChange = useCallback((h: Horizon) => {
    setHorizon(h);
    setState({ status: "idle" });
  }, []);

  return (
    <NavigationContainer>
      <Tab.Navigator
        screenOptions={({ route }) => ({
          headerShown: false,
          tabBarIcon: ({ focused, color, size }) => {
            let iconName: keyof typeof Ionicons.glyphMap = "play";
            if (route.name === "Inference") {
              iconName = focused ? "play" : "play-outline";
            } else if (route.name === "Analytics") {
              iconName = focused ? "bar-chart" : "bar-chart-outline";
            }
            return <Ionicons name={iconName} size={size} color={color} />;
          },
          tabBarActiveTintColor: "#1f6feb",
          tabBarInactiveTintColor: "gray",
        })}
      >
        <Tab.Screen name="Inference">
          {() => (
            <InferenceScreen
              chain={chain}
              horizon={horizon}
              state={state}
              onChainChange={handleChainChange}
              onHorizonChange={handleHorizonChange}
              onRun={handleRun}
              onRunAgain={handleRunAgain}
            />
          )}
        </Tab.Screen>
        <Tab.Screen name="Analytics">
          {() => (
            <AnalyticsScreen
              runs={runs}
              chain={chain}
              horizon={horizon}
              storageError={storageError}
              onChainChange={handleChainChange}
              onHorizonChange={handleHorizonChange}
            />
          )}
        </Tab.Screen>
      </Tab.Navigator>
    </NavigationContainer>
  );
}
