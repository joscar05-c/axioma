import React, { useCallback, useEffect, useState } from "react";
import {
  ActivityIndicator,
  FlatList,
  RefreshControl,
  StyleSheet,
  Text,
  View,
} from "react-native";
import { supabase } from "../lib/supabase";
import { Database } from "../types/database";

type ProblemRow = Database["public"]["Tables"]["problems"]["Row"];

export function HistoryScreen() {
  const [items, setItems] = useState<ProblemRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const loadHistory = useCallback(async () => {
    const { data } = await supabase
      .from("problems")
      .select("*")
      .order("created_at", { ascending: false })
      .limit(30);

    setItems(data ?? []);
    setLoading(false);
    setRefreshing(false);
  }, []);

  useEffect(() => {
    loadHistory();
  }, [loadHistory]);

  if (loading) {
    return (
      <View style={styles.center}>
        <ActivityIndicator color="#38bdf8" />
      </View>
    );
  }

  return (
    <FlatList
      style={styles.list}
      contentContainerStyle={styles.content}
      data={items}
      keyExtractor={(item) => item.id}
      refreshControl={
        <RefreshControl
          refreshing={refreshing}
          onRefresh={() => {
            setRefreshing(true);
            loadHistory();
          }}
          tintColor="#38bdf8"
        />
      }
      ListEmptyComponent={
        <Text style={styles.empty}>
          Aún no tienes problemas guardados en tu historial.
        </Text>
      }
      renderItem={({ item }) => (
        <View style={styles.card}>
          <View style={styles.row}>
            <Text style={styles.subject}>{item.subject.toUpperCase()}</Text>
            <Text style={styles.date}>
              {new Date(item.created_at).toLocaleDateString()}
            </Text>
          </View>
          <Text style={styles.input} numberOfLines={2}>
            {item.raw_input || "Problema escaneado por imagen"}
          </Text>
          {item.solution_summary ? (
            <Text style={styles.summary} numberOfLines={3}>
              {item.solution_summary}
            </Text>
          ) : null}
        </View>
      )}
    />
  );
}

const styles = StyleSheet.create({
  list: { flex: 1, backgroundColor: "#020617" },
  content: { padding: 16, gap: 12 },
  center: {
    flex: 1,
    backgroundColor: "#020617",
    justifyContent: "center",
    alignItems: "center",
  },
  empty: { color: "#64748b", textAlign: "center", marginTop: 40 },
  card: {
    backgroundColor: "#0f172a",
    borderRadius: 14,
    padding: 14,
    borderWidth: 1,
    borderColor: "#1e293b",
  },
  row: {
    flexDirection: "row",
    justifyContent: "space-between",
    marginBottom: 6,
  },
  subject: { color: "#38bdf8", fontSize: 12, fontWeight: "700" },
  date: { color: "#64748b", fontSize: 12 },
  input: { color: "#f8fafc", fontSize: 15, fontWeight: "600" },
  summary: { color: "#94a3b8", fontSize: 13, marginTop: 6 },
});
