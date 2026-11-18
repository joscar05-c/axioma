import React, { useEffect, useState } from "react";
import { StyleSheet, Text, TouchableOpacity, View } from "react-native";
import { SafeAreaProvider, SafeAreaView } from "react-native-safe-area-context";
import { StatusBar } from "expo-status-bar";
import { Session } from "@supabase/supabase-js";
import { supabase } from "./src/lib/supabase";
import { AuthScreen } from "./src/screens/AuthScreen";
import { HistoryScreen } from "./src/screens/HistoryScreen";
import { PaywallScreen } from "./src/screens/PaywallScreen";
import { SolverScreen } from "./src/screens/SolverScreen";

export default function App() {
  const [session, setSession] = useState<Session | null>(null);
  const [tab, setTab] = useState<"solver" | "history">("solver");
  const [paywallOpen, setPaywallOpen] = useState(false);

  useEffect(() => {
    supabase.auth.getSession().then(({ data }) => setSession(data.session));
    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange((_event, nextSession) => {
      setSession(nextSession);
    });
    return () => subscription.unsubscribe();
  }, []);

  return (
    <SafeAreaProvider>
      <SafeAreaView style={styles.root}>
        <StatusBar style="light" />
        {!session ? (
          <AuthScreen />
        ) : (
          <>
            <View style={styles.header}>
              <Text style={styles.headerTitle}>Axioma</Text>
              <TouchableOpacity onPress={() => supabase.auth.signOut()}>
                <Text style={styles.signOut}>Salir</Text>
              </TouchableOpacity>
            </View>

            <View style={styles.body}>
              {tab === "solver" ? (
                <SolverScreen
                  userId={session.user.id}
                  onOpenPaywall={() => setPaywallOpen(true)}
                />
              ) : (
                <HistoryScreen />
              )}
            </View>

            <View style={styles.tabBar}>
              <TouchableOpacity
                style={styles.tabBtn}
                onPress={() => setTab("solver")}
              >
                <Text
                  style={[styles.tabText, tab === "solver" && styles.tabActive]}
                >
                  Resolver
                </Text>
              </TouchableOpacity>
              <TouchableOpacity
                style={styles.tabBtn}
                onPress={() => setTab("history")}
              >
                <Text
                  style={[styles.tabText, tab === "history" && styles.tabActive]}
                >
                  Historial
                </Text>
              </TouchableOpacity>
            </View>

            <PaywallScreen
              visible={paywallOpen}
              onClose={() => setPaywallOpen(false)}
            />
          </>
        )}
      </SafeAreaView>
    </SafeAreaProvider>
  );
}

const styles = StyleSheet.create({
  root: { flex: 1, backgroundColor: "#020617" },
  header: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    paddingHorizontal: 18,
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: "#1e293b",
  },
  headerTitle: {
    color: "#38bdf8",
    fontSize: 20,
    fontWeight: "800",
    letterSpacing: 1.5,
  },
  signOut: { color: "#94a3b8", fontSize: 14, fontWeight: "600" },
  body: { flex: 1 },
  tabBar: {
    flexDirection: "row",
    borderTopWidth: 1,
    borderTopColor: "#1e293b",
    backgroundColor: "#0f172a",
  },
  tabBtn: { flex: 1, paddingVertical: 14, alignItems: "center" },
  tabText: { color: "#64748b", fontSize: 15, fontWeight: "700" },
  tabActive: { color: "#38bdf8" },
});
