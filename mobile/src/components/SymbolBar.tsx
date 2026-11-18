import React from "react";
import { ScrollView, StyleSheet, Text, TouchableOpacity } from "react-native";

interface SymbolBarProps {
  onInsert: (token: string) => void;
}

const QUICK_TOKENS = [
  { label: "∫", value: "integrate(, x)" },
  { label: "d/dx", value: "d/dx " },
  { label: "lim", value: "lim(x->0) " },
  { label: "x²", value: "^2" },
  { label: "√", value: "sqrt()" },
  { label: "π", value: "pi" },
  { label: "e^x", value: "exp(x)" },
  { label: "→", value: " -> " },
  { label: "Δ", value: "Delta " },
];

export function SymbolBar({ onInsert }: SymbolBarProps) {
  return (
    <ScrollView
      horizontal
      showsHorizontalScrollIndicator={false}
      contentContainerStyle={styles.row}
    >
      {QUICK_TOKENS.map((item) => (
        <TouchableOpacity
          key={item.label}
          style={styles.chip}
          onPress={() => onInsert(item.value)}
        >
          <Text style={styles.chipText}>{item.label}</Text>
        </TouchableOpacity>
      ))}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  row: {
    gap: 8,
    paddingVertical: 8,
  },
  chip: {
    backgroundColor: "#1e293b",
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: "#334155",
  },
  chipText: {
    color: "#e2e8f0",
    fontSize: 14,
    fontWeight: "600",
  },
});
