import mimetypes
from google import genai
from google.genai import types
from app.core.config import get_settings
from app.schemas.solve import AIPlanOutput

_SYSTEM_PROMPT = """Eres el analizador científico de Axioma.
Tu trabajo es interpretar problemas de Matemáticas, Física, Química e Ingeniería (en texto, LaTeX o imagen)
y producir un plan JSON estructurado en español para que los motores simbólicos de Python verifiquen el cálculo exacto.

Reglas estrictas:
1. Clasifica `subject` en: "math", "physics", "chemistry" o "engineering".
2. Elige `engine`:
   - "math": derivadas, integrales, límites, álgebra, ecuaciones, EDOs, matrices.
     Usa sintaxis Python/SymPy válida en `expression` (ej. "x**2 * sin(x)", "Derivative(y(x), x) + 2*y(x) = 0").
   - "physics": problemas con fórmulas y unidades físicas. Completa `physics_equation` (ej. "F = m * a"),
     `physics_target` (ej. "F"), `physics_knowns` (ej. {"m": "10 kg", "a": "9.81 m/s**2"}), y `physics_output_unit` (ej. "N").
   - "chemistry": balanceo de reacciones (`chem_reactants`, `chem_products`, ej. ["H2", "O2"] -> ["H2O"])
     o masa molar (`chem_formula`, ej. "H2SO4").
   - "ai_only": solo si el problema es conceptual/teórico o de ingeniería multi-etapa que no encaja en una sola llamada de los motores anteriores.
     En ese caso proporciona `ai_result_latex` con el resultado final en LaTeX limpio.
3. Redacta `steps` claros y pedagógicos en español con `title`, `explanation` y `expression_latex`.
4. `extracted_problem` debe transcribir claramente el enunciado o fórmula detectada.
"""


def _guess_mime_type(image_path: str) -> str:
    mime, _ = mimetypes.guess_type(image_path)
    if mime in ("image/jpeg", "image/png", "image/webp"):
        return mime
    return "image/jpeg"


def analyze_problem_with_gemini(
    raw_input: str | None,
    subject_hint: str = "auto",
    image_bytes: bytes | None = None,
    image_path: str | None = None,
) -> AIPlanOutput:
    """Call Google Gemini multimodal API with structured JSON output."""
    settings = get_settings()
    if not settings.gemini_api_key:
        raise RuntimeError("GEMINI_API_KEY is not configured on the server.")

    client = genai.Client(api_key=settings.gemini_api_key)

    contents: list[object] = []
    prompt_parts = [f"Pista de materia del usuario: {subject_hint}."]
    if raw_input:
        prompt_parts.append(f"Enunciado / expresión del usuario:\n{raw_input}")
    else:
        prompt_parts.append("Lee y resuelve el problema mostrado en la imagen adjunta.")
    contents.append("\n\n".join(prompt_parts))

    if image_bytes is not None:
        contents.append(
            types.Part.from_bytes(
                data=image_bytes,
                mime_type=_guess_mime_type(image_path or "problem.jpg"),
            )
        )

    response = client.models.generate_content(
        model=settings.gemini_model,
        contents=contents,
        config=types.GenerateContentConfig(
            system_instruction=_SYSTEM_PROMPT,
            response_mime_type="application/json",
            response_schema=AIPlanOutput,
            temperature=0.1,
        ),
    )

    if response.parsed is not None and isinstance(response.parsed, AIPlanOutput):
        return response.parsed
    return AIPlanOutput.model_validate_json(response.text)
