"""Compara varios modelos de Ollama ejecutando las mismas pruebas sobre el agente.

Uso:
    python eval_models.py                                   # todos los modelos, todas las pruebas
    python eval_models.py qwen3.5:4b bonsai-2:9b            # modelos concretos
    python eval_models.py --rapido qwen3.5:4b               # solo 3 pruebas clave (CPU lenta)
"""

from __future__ import annotations

import json
import sys
import time
import unicodedata
from datetime import date

from strands import Agent

from agent import SYSTEM_PROMPT, TOOLS, create_model

DEFAULT_MODELS = [
    "qwen3.5:4b",
    "bonsai-2:9b",
    "nemotron-3-nano:4b",
    "gemma4:e2b",
    "gemma4:e4b",
    "lfm3:1.7b",
]

SEARCH = "search_conference_sessions"
DETAIL = "get_conference_session"
NOW = "get_current_datetime"

# expected_tools: tools que deben aparecer (set vacío = no debe usar ninguna).
# must_contain: todas deben estar en la respuesta. any_of: basta con una.
TEST_CASES = [
    {
        "name": "una_tool",
        "question": "¿Qué charlas hay de seguridad?",
        "expected_tools": {SEARCH},
        "must_contain": ["hardening", "sala a"],
    },
    {
        "name": "filtro_fecha",
        "question": "¿Qué charlas hay el 11 de noviembre de 2026?",
        "expected_tools": {SEARCH},
        "must_contain": ["hardening", "prometheus"],
    },
    {
        "name": "encadenar_tools",
        "question": "¿Quién da la charla de Kubernetes y qué experiencia tiene?",
        "expected_tools": {SEARCH, DETAIL},
        "must_contain": ["lucia", "sre"],
    },
    {
        "name": "fecha_actual",
        "question": "¿Cuántos días faltan desde hoy para la charla de Kubernetes?",
        "expected_tools": {NOW, SEARCH},
        "must_contain": [str((date(2026, 11, 10) - date.today()).days)],
    },
    {
        "name": "no_inventar",
        "question": "¿Hay alguna charla sobre blockchain?",
        "expected_tools": {SEARCH},
        "any_of": ["no hay", "no encontr", "ninguna", "no existe", "no tengo", "no figura"],
    },
    {
        "name": "sin_tools",
        "question": "Hola, ¿qué puedes hacer por mí?",
        "expected_tools": set(),
    },
]

# Las 3 que más discriminan: usar una tool, encadenar dos y no inventar.
QUICK_CASES = {"una_tool", "encadenar_tools", "no_inventar"}


def create_light_model(model_id: str):
    model = create_model(model_id)
    # Con CPU: respuestas cortas y contexto pequeño (los datos de prueba caben de sobra).
    model.update_config(max_tokens=512, options={"num_ctx": 4096})
    return model


def normalize(text: str) -> str:
    text = unicodedata.normalize("NFKD", text.lower())
    return "".join(char for char in text if not unicodedata.combining(char))


def called_tools(agent: Agent) -> list[str]:
    return [
        block["toolUse"]["name"]
        for message in agent.messages
        for block in message.get("content", [])
        if "toolUse" in block
    ]


def run_case(model_id: str, case: dict) -> dict:
    agent = Agent(
        model=create_light_model(model_id),
        tools=TOOLS,
        system_prompt=SYSTEM_PROMPT,
        callback_handler=None,
    )
    start = time.perf_counter()
    try:
        answer = str(agent(case["question"]))
        error = None
    except Exception as exc:  # Algunos modelos generan tool calls mal formadas.
        answer, error = "", f"{type(exc).__name__}: {exc}"
    elapsed = time.perf_counter() - start

    tools = called_tools(agent)
    expected = case["expected_tools"]
    tools_ok = expected <= set(tools) if expected else not tools
    text = normalize(answer)
    content_ok = all(normalize(word) in text for word in case.get("must_contain", []))
    if "any_of" in case:
        content_ok = content_ok and any(normalize(word) in text for word in case["any_of"])

    return {
        "case": case["name"],
        "tools_ok": tools_ok,
        "content_ok": content_ok and error is None,
        "tools": tools,
        "seconds": round(elapsed, 1),
        "error": error,
        "answer": answer.strip(),
    }


def warm_up(model_id: str) -> None:
    # La primera llamada carga el modelo en RAM; no debe contar en los tiempos.
    Agent(model=create_light_model(model_id), callback_handler=None)("Responde solo: OK")


def main() -> None:
    args = sys.argv[1:]
    quick = "--rapido" in args
    models = [arg for arg in args if arg != "--rapido"] or DEFAULT_MODELS
    cases = [case for case in TEST_CASES if not quick or case["name"] in QUICK_CASES]
    report: dict[str, list[dict]] = {}

    for model_id in models:
        print(f"\n=== {model_id} ===")
        try:
            warm_up(model_id)
        except Exception as exc:
            print(f"  No se pudo cargar: {exc}")
            continue
        report[model_id] = []
        for case in cases:
            result = run_case(model_id, case)
            report[model_id].append(result)
            status = "OK " if result["tools_ok"] and result["content_ok"] else "FAIL"
            print(
                f"  [{status}] {case['name']:<16} {result['seconds']:>6}s  "
                f"tools={result['tools']}" + (f"  error={result['error']}" if result["error"] else "")
            )

    print("\n=== Ranking ===")
    print(f"{'modelo':<22}{'puntos':>8}{'tools':>8}{'resp.':>8}{'t. medio':>10}")
    rows = []
    for model_id, results in report.items():
        tools_ok = sum(r["tools_ok"] for r in results)
        content_ok = sum(r["content_ok"] for r in results)
        avg = sum(r["seconds"] for r in results) / len(results)
        rows.append((tools_ok + content_ok, -avg, model_id, tools_ok, content_ok, avg))
    total = len(cases)
    for score, _, model_id, tools_ok, content_ok, avg in sorted(rows, reverse=True):
        print(
            f"{model_id:<22}{score:>5}/{total * 2:<2}{tools_ok:>5}/{total:<2}"
            f"{content_ok:>5}/{total:<2}{avg:>9.1f}s"
        )

    with open("eval_results.json", "w", encoding="utf-8") as file:
        json.dump(report, file, ensure_ascii=False, indent=2)
    print("\nDetalle con las respuestas completas en eval_results.json")


if __name__ == "__main__":
    main()
