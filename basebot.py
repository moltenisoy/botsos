import json
import asyncio
from browser_use import Agent, Browser
import ollama  # Cliente para Ollama

# Cargar rutinas preestablecidas
with open('rutinas.json', 'r') as f:
    rutinas = json.load(f)

async def youtube_agent(rutina_id):
    # Configurar navegador embebido (Chromium headless=False para ver)
    browser = Browser(headless=False)  # Visible para debug
    llm = ollama.Client()  # Conecta a Ollama local

    # Agente IA
    agent = Agent(
        task=f"Ejecuta rutina {rutina_id} en YouTube: {rutinas[rutina_id]['descripcion']}",
        llm=llm,  # Usa Phi-3 via Ollama
        browser=browser,
        model="microsoft/phi-3-mini"  # LLM local
    )

    # Prompt preestablecido para LLM (tú defines lógica)
    prompt = f"""
    Analiza la página de YouTube con HTML actual.
    Rutina: {rutinas[rutina_id]['acciones']}.
    Reglas:
    - Busca: Escribe '{rutinas[rutina_id]['query']}' en buscador, abre primer video NO ad.
    - Reproduce: Click play, espera {rutinas[rutina_id]['tiempo']} seg.
    - Pausa/Cierra/Repite: Según timer.
    - Ad: Si ves 'Skip ad', clickea.
    - Comenta: Click comentario, escribe '{rutinas[rutina_id]['comentario']}', submit.
    - Like: Click like.
    Solo acciones predefinidas. No improvises.
    Devuelve acciones JSON: {{"action": "click|type|wait", "selector": "descripcion", "value": "texto"}}.
    """

    # Ejecutar agente
    history = await agent.run(prompt=prompt)
    print(history)  # Log de acciones

    await browser.close()

# Rutina ejemplo en rutinas.json
# {
#   "rutina1": {
#     "descripcion": "Buscar video, reproducir 30s, pausar, like, comentar",
#     "query": "tutorial python",
#     "tiempo": 30,
#     "comentario": "¡Excelente video!",
#     "acciones": ["buscar", "reproducir", "pausar", "like", "comentar"]
#   }
# }

# Correr (para múltiples: usa asyncio.gather)
if __name__ == "__main__":
    asyncio.run(youtube_agent("rutina1"))