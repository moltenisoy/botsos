"""
BotSOS-LMStudio - Base Bot Example

Este archivo muestra un ejemplo básico de cómo usar LM Studio
con la API compatible con OpenAI para automatización de navegador.
"""

import json
import asyncio
from browser_use import Agent, Browser
import openai  # Cliente OpenAI para LM Studio

# Configuración de LM Studio
LMSTUDIO_BASE_URL = "http://localhost:1234/v1"
LMSTUDIO_API_KEY = "lm-studio"  # LM Studio no requiere API key real

# Crear cliente de LM Studio
client = openai.OpenAI(
    base_url=LMSTUDIO_BASE_URL,
    api_key=LMSTUDIO_API_KEY
)

# Cargar rutinas preestablecidas
with open('config/rutinas.json', 'r') as f:
    rutinas = json.load(f)


def get_llm_response(prompt: str, model: str = "local-model") -> str:
    """Obtener respuesta del modelo LLM a través de LM Studio."""
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "Eres un asistente de automatización de navegador."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=2048
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Error al comunicarse con LM Studio: {e}")
        return ""


async def youtube_agent(rutina_id):
    """Ejecutar una rutina de automatización de YouTube."""
    # Configurar navegador embebido (Chromium headless=False para ver)
    browser = Browser(headless=False)  # Visible para debug

    # Agente IA usando LM Studio
    agent = Agent(
        task=f"Ejecuta rutina {rutina_id} en YouTube: {rutinas[rutina_id]['descripcion']}",
        llm=client,  # Usa LM Studio via API OpenAI
        browser=browser,
        model="local-model"  # El modelo cargado en LM Studio
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


def check_lmstudio_connection():
    """Verificar conexión con LM Studio."""
    try:
        models = client.models.list()
        if models.data:
            print("✓ Conexión con LM Studio establecida")
            print("  Modelos disponibles:")
            for model in models.data:
                print(f"    - {model.id}")
            return True
        else:
            print("⚠️ LM Studio está ejecutándose pero no hay modelos cargados")
            return False
    except Exception as e:
        print(f"✗ No se pudo conectar con LM Studio: {e}")
        print("  Asegúrese de que LM Studio esté ejecutándose con el servidor local activo")
        return False


# Rutina ejemplo en config/rutinas.json
# {
#   "rutinas": {
#     "rutina1": {
#       "id": "rutina1",
#       "nombre": "Rutina de Ejemplo",
#       "descripcion": "Buscar video, reproducir 30s, pausar, like, comentar",
#       "query": "tutorial python",
#       "tiempo": 30,
#       "comentario": "¡Excelente video!",
#       "acciones": ["buscar", "reproducir", "pausar", "like", "comentar"]
#     }
#   }
# }

# Correr (para múltiples: usa asyncio.gather)
if __name__ == "__main__":
    print("BotSOS-LMStudio - Base Bot")
    print("==========================")
    
    if check_lmstudio_connection():
        asyncio.run(youtube_agent("rutina1"))