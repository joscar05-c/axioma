import { supabase } from "./supabase";

export type SubjectType = "math" | "physics" | "chemistry" | "engineering";

export interface SolveStep {
  title: string;
  explanation: string;
  expression_latex?: string | null;
}

export interface PlotData {
  variable: string;
  expression_latex: string;
  x: number[];
  y: number[];
}

export interface QuotaStatus {
  plan_tier: "free" | "pro";
  daily_limit: number | null;
  used_today: number;
  remaining_today: number | null;
}

export interface SolveResponse {
  problem_id: string | null;
  subject: SubjectType;
  extracted_problem: string;
  verified: boolean;
  verified_result_latex: string;
  solution_summary: string;
  steps: SolveStep[];
  steps_locked: boolean;
  plot_data: PlotData | null;
  plot_locked: boolean;
  quota: QuotaStatus;
}

export class UpgradeRequiredError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "UpgradeRequiredError";
  }
}

export const API_URL = (
  process.env.EXPO_PUBLIC_API_URL ?? "https://axioma-api.vercel.app"
).replace(/\/$/, "");

async function getAuthHeaders(): Promise<Record<string, string>> {
  const {
    data: { session },
  } = await supabase.auth.getSession();

  if (!session?.access_token) {
    throw new Error("Debes iniciar sesión para continuar.");
  }

  return {
    "Content-Type": "application/json",
    Authorization: `Bearer ${session.access_token}`,
  };
}

export async function fetchQuota(): Promise<QuotaStatus> {
  const headers = await getAuthHeaders();
  const resp = await fetch(`${API_URL}/api/v1/me/quota`, { headers });
  if (!resp.ok) {
    throw new Error("No se pudo consultar la cuota del usuario.");
  }
  return resp.json();
}

export async function solveProblem(params: {
  subject_hint: SubjectType | "auto";
  input_type: "text" | "latex" | "image";
  raw_input?: string;
  image_path?: string;
}): Promise<SolveResponse> {
  const headers = await getAuthHeaders();
  const resp = await fetch(`${API_URL}/api/v1/solve`, {
    method: "POST",
    headers,
    body: JSON.stringify(params),
  });

  if (resp.status === 402) {
    const errBody = await resp.json().catch(() => ({}));
    const msg =
      errBody?.detail?.message ??
      "Alcanzaste tu límite diario gratuito. Actualiza a Axioma Pro.";
    throw new UpgradeRequiredError(msg);
  }

  if (!resp.ok) {
    const errBody = await resp.json().catch(() => ({}));
    throw new Error(errBody?.detail ?? "Error al resolver el problema.");
  }

  return resp.json();
}

export async function uploadProblemImage(
  userId: string,
  uri: string
): Promise<string> {
  const ext = uri.split(".").pop()?.toLowerCase() === "png" ? "png" : "jpg";
  const mimeType = ext === "png" ? "image/png" : "image/jpeg";
  const filePath = `${userId}/${Date.now()}.${ext}`;

  const response = await fetch(uri);
  const arrayBuffer = await response.arrayBuffer();

  const { error } = await supabase.storage
    .from("problem-images")
    .upload(filePath, arrayBuffer, {
      contentType: mimeType,
      upsert: false,
    });

  if (error) {
    throw new Error(`No se pudo subir la imagen: ${error.message}`);
  }

  return filePath;
}
