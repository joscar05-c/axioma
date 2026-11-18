import React from "react";
import { StyleSheet, Text, View } from "react-native";
import Svg, { Line, Polyline } from "react-native-svg";
import { PlotData } from "../lib/api";

interface PlotRendererProps {
  plot: PlotData;
}

export function PlotRenderer({ plot }: PlotRendererProps) {
  const width = 320;
  const height = 180;
  const padding = 16;

  if (plot.x.length < 2 || plot.y.length < 2) {
    return null;
  }

  const minX = Math.min(...plot.x);
  const maxX = Math.max(...plot.x);
  const minY = Math.min(...plot.y);
  const maxY = Math.max(...plot.y);
  const spanX = maxX - minX || 1;
  const spanY = maxY - minY || 1;

  const toSvgX = (x: number) =>
    padding + ((x - minX) / spanX) * (width - padding * 2);
  const toSvgY = (y: number) =>
    height - padding - ((y - minY) / spanY) * (height - padding * 2);

  const points = plot.x
    .map((x, idx) => `${toSvgX(x).toFixed(1)},${toSvgY(plot.y[idx]).toFixed(1)}`)
    .join(" ");

  const zeroY = minY <= 0 && maxY >= 0 ? toSvgY(0) : null;
  const zeroX = minX <= 0 && maxX >= 0 ? toSvgX(0) : null;

  return (
    <View style={styles.card}>
      <Text style={styles.title}>Gráfica 2D ({plot.variable})</Text>
      <Svg width="100%" height={height} viewBox={`0 0 ${width} ${height}`}>
        {zeroY !== null && (
          <Line
            x1={padding}
            y1={zeroY}
            x2={width - padding}
            y2={zeroY}
            stroke="#334155"
            strokeWidth="1"
          />
        )}
        {zeroX !== null && (
          <Line
            x1={zeroX}
            y1={padding}
            x2={zeroX}
            y2={height - padding}
            stroke="#334155"
            strokeWidth="1"
          />
        )}
        <Polyline
          fill="none"
          stroke="#38bdf8"
          strokeWidth="2.5"
          points={points}
        />
      </Svg>
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    backgroundColor: "#0f172a",
    borderRadius: 12,
    borderWidth: 1,
    borderColor: "#1e293b",
    padding: 12,
    marginTop: 12,
  },
  title: {
    color: "#94a3b8",
    fontSize: 12,
    fontWeight: "600",
    marginBottom: 8,
  },
});
