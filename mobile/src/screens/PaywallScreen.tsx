import React from "react";
import {
  Alert,
  Modal,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from "react-native";

interface PaywallScreenProps {
  visible: boolean;
  onClose: () => void;
}

export function PaywallScreen({ visible, onClose }: PaywallScreenProps) {
  function handleSubscribe() {
    Alert.alert(
      "Integración de pagos pendiente",
      "En la siguiente fase conectaremos RevenueCat / Stripe para activar Axioma Pro automáticamente vía webhook en Supabase."
    );
  }

  return (
    <Modal visible={visible} animationType="slide" transparent>
      <View style={styles.overlay}>
        <View style={styles.sheet}>
          <Text style={styles.badge}>AXIOMA PRO</Text>
          <Text style={styles.title}>Desbloquea todo el poder científico</Text>

          <View style={styles.featureList}>
            <Text style={styles.feature}>• Resoluciones diarias ilimitadas</Text>
            <Text style={styles.feature}>
              • Procedimiento paso a paso detallado en español
            </Text>
            <Text style={styles.feature}>• Gráficas 2D interactivas</Text>
            <Text style={styles.feature}>
              • Cálculo simbólico, Física con unidades y Química avanzada
            </Text>
          </View>

          <TouchableOpacity style={styles.ctaBtn} onPress={handleSubscribe}>
            <Text style={styles.ctaText}>Actualizar a Axioma Pro</Text>
          </TouchableOpacity>

          <TouchableOpacity style={styles.closeBtn} onPress={onClose}>
            <Text style={styles.closeText}>Seguir con Plan Gratis</Text>
          </TouchableOpacity>
        </View>
      </View>
    </Modal>
  );
}

const styles = StyleSheet.create({
  overlay: {
    flex: 1,
    backgroundColor: "rgba(2, 6, 23, 0.85)",
    justifyContent: "flex-end",
  },
  sheet: {
    backgroundColor: "#0f172a",
    borderTopLeftRadius: 24,
    borderTopRightRadius: 24,
    padding: 24,
    borderTopWidth: 1,
    borderColor: "#1e293b",
  },
  badge: {
    color: "#38bdf8",
    fontWeight: "800",
    fontSize: 12,
    letterSpacing: 2,
  },
  title: {
    color: "#f8fafc",
    fontSize: 24,
    fontWeight: "800",
    marginTop: 8,
  },
  featureList: { marginVertical: 20, gap: 10 },
  feature: { color: "#cbd5e1", fontSize: 15 },
  ctaBtn: {
    backgroundColor: "#38bdf8",
    borderRadius: 14,
    paddingVertical: 15,
    alignItems: "center",
  },
  ctaText: { color: "#020617", fontSize: 16, fontWeight: "800" },
  closeBtn: { paddingVertical: 14, alignItems: "center", marginTop: 4 },
  closeText: { color: "#94a3b8", fontSize: 14, fontWeight: "600" },
});
