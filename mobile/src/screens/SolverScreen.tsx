import React, { useEffect, useState } from "react";
import {
  ActivityIndicator,
  Alert,
  Image,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  TouchableOpacity,
  View,
} from "react-native";
import * as ImagePicker from "expo-image-picker";
import { MathRenderer } from "../components/MathRenderer";
import { PlotRenderer } from "../components/PlotRenderer";
import { SymbolBar } from "../components/SymbolBar";
import {
  fetchQuota,
  QuotaStatus,
  solveProblem,
  SolveResponse,
  SubjectType,
  UpgradeRequiredError,
  uploadProblemImage,
} from "../lib/api";

interface SolverScreenProps {
  userId: string;
  onOpenPaywall: () => void;
}

const SUBJECTS: Array<{ key: SubjectType | "auto"; label: string }> = [
  { key: "auto", label: "Auto" },
  { key: "math", label: "Mate / Cálculo" },
  { key: "physics", label: "Física" },
  { key: "chemistry", label: "Química" },
  { key: "engineering", label: "Ingeniería" },
];

export function SolverScreen({ userId, onOpenPaywall }: SolverScreenProps) {
  const [subject, setSubject] = useState<SubjectType | "auto">("auto");
  const [rawInput, setRawInput] = useState("");
  const [selectedImageUri, setSelectedImageUri] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<SolveResponse | null>(null);
  const [quota, setQuota] = useState<QuotaStatus | null>(null);

  useEffect(() => {
    fetchQuota().then(setQuota).catch(() => {});
  }, []);

  async function pickImage(useCamera: boolean) {
    const perm = useCamera
      ? await ImagePicker.requestCameraPermissionsAsync()
      : await ImagePicker.requestMediaLibraryPermissionsAsync();

    if (!perm.granted) {
      Alert.alert(
        "Permiso requerido",
        "Autoriza el acceso a cámara o galería para escanear ejercicios."
      );
      return;
    }

    const picked = useCamera
      ? await ImagePicker.launchCameraAsync({ quality: 0.85 })
      : await ImagePicker.launchImageLibraryAsync({ quality: 0.85 });

    if (!picked.canceled && picked.assets[0]?.uri) {
      setSelectedImageUri(picked.assets[0].uri);
    }
  }

  async function handleSolve() {
    if (!rawInput.trim() && !selectedImageUri) {
      Alert.alert(
        "Ingresa un problema",
        "Escribe una ecuación/enunciado o sube una foto."
      );
      return;
    }

    setLoading(true);
    try {
      let imagePath: string | undefined;
      if (selectedImageUri) {
        imagePath = await uploadProblemImage(userId, selectedImageUri);
      }

      const response = await solveProblem({
        subject_hint: subject,
        input_type: imagePath ? "image" : "text",
        raw_input: rawInput.trim() || undefined,
        image_path: imagePath,
      });

      setResult(response);
      setQuota(response.quota);
    } catch (err) {
      if (err instanceof UpgradeRequiredError) {
        onOpenPaywall();
        return;
      }
      const message =
        err instanceof Error ? err.message : "Error inesperado al resolver.";
      Alert.alert("No se pudo resolver", message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <ScrollView
      style={styles.container}
      contentContainerStyle={styles.content}
      keyboardShouldPersistTaps="handled"
    >
      <View style={styles.quotaBar}>
        <Text style={styles.quotaText}>
          {quota?.plan_tier === "pro"
            ? "Axioma Pro · Ilimitado"
            : `Plan Gratis · ${quota?.remaining_today ?? 5}/${quota?.daily_limit ?? 5} restantes hoy`}
        </Text>
        {quota?.plan_tier !== "pro" && (
          <TouchableOpacity onPress={onOpenPaywall}>
            <Text style={styles.upgradeLink}>Pasar a Pro</Text>
          </TouchableOpacity>
        )}
      </View>

      <ScrollView
        horizontal
        showsHorizontalScrollIndicator={false}
        contentContainerStyle={styles.subjectRow}
      >
        {SUBJECTS.map((item) => {
          const active = item.key === subject;
          return (
            <TouchableOpacity
              key={item.key}
              style={[styles.subjectChip, active && styles.subjectChipActive]}
              onPress={() => setSubject(item.key)}
            >
              <Text
                style={[styles.subjectText, active && styles.subjectTextActive]}
              >
                {item.label}
              </Text>
            </TouchableOpacity>
          );
        })}
      </ScrollView>

      <TextInput
        style={styles.input}
        placeholder="Ej: integral de x^2 * sin(x), o un enunciado de física o química..."
        placeholderTextColor="#64748b"
        multiline
        value={rawInput}
        onChangeText={setRawInput}
      />

      <SymbolBar onInsert={(token) => setRawInput((prev) => prev + token)} />

      <View style={styles.mediaRow}>
        <TouchableOpacity
          style={styles.secondaryBtn}
          onPress={() => pickImage(true)}
        >
          <Text style={styles.secondaryBtnText}>Cámara</Text>
        </TouchableOpacity>
        <TouchableOpacity
          style={styles.secondaryBtn}
          onPress={() => pickImage(false)}
        >
          <Text style={styles.secondaryBtnText}>Galería</Text>
        </TouchableOpacity>
      </View>

      {selectedImageUri && (
        <View style={styles.previewCard}>
          <Image source={{ uri: selectedImageUri }} style={styles.previewImg} />
          <TouchableOpacity onPress={() => setSelectedImageUri(null)}>
            <Text style={styles.removeImg}>Quitar imagen</Text>
          </TouchableOpacity>
        </View>
      )}

      <TouchableOpacity
        style={styles.solveBtn}
        onPress={handleSolve}
        disabled={loading}
      >
        {loading ? (
          <ActivityIndicator color="#020617" />
        ) : (
          <Text style={styles.solveBtnText}>Resolver con Axioma</Text>
        )}
      </TouchableOpacity>

      {result && (
        <View style={styles.resultBox}>
          <View style={styles.resultHeader}>
            <Text style={styles.resultTitle}>Resultado</Text>
            <Text style={styles.badge}>
              {result.verified ? "Verificado en Python" : "Análisis IA"}
            </Text>
          </View>

          <MathRenderer latex={result.verified_result_latex} />

          <Text style={styles.summaryText}>{result.solution_summary}</Text>

          {result.steps_locked ? (
            <TouchableOpacity
              style={styles.lockCard}
              onPress={onOpenPaywall}
            >
              <Text style={styles.lockTitle}>
                Paso a paso completo bloqueado (Axioma Pro)
              </Text>
              <Text style={styles.lockSubtitle}>
                Desbloquea cada paso detallado y gráficas interactivas
              </Text>
            </TouchableOpacity>
          ) : (
            result.steps.map((step, index) => (
              <View key={index} style={styles.stepCard}>
                <Text style={styles.stepTitle}>
                  {index + 1}. {step.title}
                </Text>
                <Text style={styles.stepBody}>{step.explanation}</Text>
                {step.expression_latex ? (
                  <MathRenderer latex={step.expression_latex} height={64} fontSize={15} />
                ) : null}
              </View>
            ))
          )}

          {result.plot_data && <PlotRenderer plot={result.plot_data} />}
        </View>
      )}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: "#020617" },
  content: { padding: 16, paddingBottom: 32 },
  quotaBar: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    backgroundColor: "#0f172a",
    padding: 12,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: "#1e293b",
    marginBottom: 12,
  },
  quotaText: { color: "#cbd5e1", fontSize: 13, fontWeight: "600" },
  upgradeLink: { color: "#38bdf8", fontSize: 13, fontWeight: "700" },
  subjectRow: { gap: 8, marginBottom: 12 },
  subjectChip: {
    paddingHorizontal: 14,
    paddingVertical: 8,
    borderRadius: 20,
    backgroundColor: "#0f172a",
    borderWidth: 1,
    borderColor: "#1e293b",
  },
  subjectChipActive: {
    backgroundColor: "#0284c7",
    borderColor: "#38bdf8",
  },
  subjectText: { color: "#94a3b8", fontSize: 13, fontWeight: "600" },
  subjectTextActive: { color: "#f8fafc" },
  input: {
    minHeight: 110,
    backgroundColor: "#0f172a",
    color: "#f8fafc",
    borderRadius: 14,
    borderWidth: 1,
    borderColor: "#1e293b",
    padding: 14,
    fontSize: 16,
    textAlignVertical: "top",
  },
  mediaRow: { flexDirection: "row", gap: 10, marginTop: 8 },
  secondaryBtn: {
    flex: 1,
    backgroundColor: "#1e293b",
    paddingVertical: 12,
    borderRadius: 12,
    alignItems: "center",
  },
  secondaryBtnText: { color: "#e2e8f0", fontWeight: "600" },
  previewCard: {
    marginTop: 12,
    backgroundColor: "#0f172a",
    padding: 10,
    borderRadius: 12,
    alignItems: "center",
  },
  previewImg: { width: "100%", height: 160, borderRadius: 8 },
  removeImg: { color: "#f87171", marginTop: 8, fontWeight: "600" },
  solveBtn: {
    backgroundColor: "#38bdf8",
    paddingVertical: 15,
    borderRadius: 14,
    alignItems: "center",
    marginTop: 14,
  },
  solveBtnText: { color: "#020617", fontSize: 16, fontWeight: "800" },
  resultBox: {
    marginTop: 20,
    backgroundColor: "#0b1120",
    borderRadius: 16,
    padding: 14,
    borderWidth: 1,
    borderColor: "#1e293b",
  },
  resultHeader: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: 10,
  },
  resultTitle: { color: "#f8fafc", fontSize: 18, fontWeight: "700" },
  badge: {
    color: "#34d399",
    fontSize: 12,
    fontWeight: "700",
    backgroundColor: "#064e3b",
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 8,
  },
  summaryText: { color: "#cbd5e1", marginTop: 12, fontSize: 14, lineHeight: 20 },
  lockCard: {
    marginTop: 14,
    backgroundColor: "#172554",
    borderWidth: 1,
    borderColor: "#1d4ed8",
    borderRadius: 12,
    padding: 14,
  },
  lockTitle: { color: "#93c5fd", fontWeight: "700", fontSize: 14 },
  lockSubtitle: { color: "#bfdbfe", fontSize: 12, marginTop: 4 },
  stepCard: {
    marginTop: 12,
    backgroundColor: "#0f172a",
    borderRadius: 12,
    padding: 12,
    borderWidth: 1,
    borderColor: "#1e293b",
    gap: 8,
  },
  stepTitle: { color: "#38bdf8", fontWeight: "700", fontSize: 14 },
  stepBody: { color: "#cbd5e1", fontSize: 14, lineHeight: 20 },
});
