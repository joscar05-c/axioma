import React from "react";
import { StyleSheet, View } from "react-native";
import { WebView } from "react-native-webview";

interface MathRendererProps {
  latex: string;
  height?: number;
  fontSize?: number;
}

export function MathRenderer({
  latex,
  height = 84,
  fontSize = 18,
}: MathRendererProps) {
  const escapedLatex = JSON.stringify(latex);

  const html = `<!DOCTYPE html>
<html>
  <head>
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0" />
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/katex.min.css" />
    <script src="https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/katex.min.js"></script>
    <style>
      body {
        margin: 0;
        padding: 8px 12px;
        background-color: transparent;
        color: #f8fafc;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: ${fontSize}px;
        overflow-x: auto;
      }
      #math {
        width: 100%;
        text-align: center;
      }
    </style>
  </head>
  <body>
    <div id="math"></div>
    <script>
      try {
        katex.render(${escapedLatex}, document.getElementById("math"), {
          displayMode: true,
          throwOnError: false
        });
      } catch (e) {
        document.getElementById("math").textContent = ${escapedLatex};
      }
    </script>
  </body>
</html>`;

  return (
    <View style={[styles.container, { height }]}>
      <WebView
        originWhitelist={["*"]}
        source={{ html }}
        style={styles.webview}
        scrollEnabled={true}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    width: "100%",
    backgroundColor: "#0f172a",
    borderRadius: 12,
    overflow: "hidden",
    borderWidth: 1,
    borderColor: "#1e293b",
  },
  webview: {
    backgroundColor: "transparent",
  },
});
