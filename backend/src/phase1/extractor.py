"""
extractor.py - Phase 1: LLM-based clinical concept extraction

Extracts medical concepts from clinical text and assigns OMOP domains.
Uses Pydantic schemas for structured output (no manual JSON parsing).

Supports: OpenAI GPT-4, Ollama (local)
"""

import os
import sys
import json
from typing import List, Dict, Optional
from pathlib import Path
from datetime import datetime

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from src.phase1.prompts import EXTRACTION_SYSTEM_PROMPT
from src.phase1.schema import ExtractionResult

# Load .env file
env_path = Path(__file__).parent.parent.parent / '.env'
load_dotenv(env_path)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY not found in environment variables")


# Windows encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

def get_llm(source: str = "openai", temperature=0.0):
    """
    Initialize a language model based on the specified source.
    
    Args:
        source (str): LLM provider - "openai" or "groq"
        temperature (float): Sampling temperature for text generation
        
    Returns:
        LangChain LLM instance
        
    Raises:
        ValueError: If unsupported source is provided
    """
    try:
        if source == "openai":
            if not OPENAI_API_KEY:
                raise ValueError("OPENAI_API_KEY not found in environment variables")
            return ChatOpenAI(model="gpt-4o-mini", temperature=temperature)
        else:
            raise ValueError(f"Unsupported source: {source}")
    except Exception as e:
        raise RuntimeError(f"Failed to initialize LLM: {e}")


def create_parser(): 
    return PydanticOutputParser(pydantic_object=ExtractionResult)

def prompt(): 
    parser = create_parser()

    prompt = ChatPromptTemplate.from_template(
        template=EXTRACTION_SYSTEM_PROMPT,
        partial_variables={"format_instructions": parser.get_format_instructions()}
    )

    return prompt


def extract_medical_entities(clinical_text: str,
                             reference_date: Optional[str] = None,
                             source: str = "openai",
                             temperature: float = 0.0) -> Dict:
    # Reason: reference_date is needed for resolving relative temporal expressions ("hace 3 meses")
    if reference_date is None:
        reference_date = datetime.now().strftime("%Y-%m-%d")

    llm = get_llm(source, temperature)
    parser = create_parser()
    extraction_prompt = prompt()
    chain = extraction_prompt | llm | parser
    result = chain.invoke({
        "clinical_text": clinical_text,
        "reference_date": reference_date
    })
    return result.model_dump(exclude_none=False)



def visual_json(result: Dict):
    """
    Convert the extracted entities to a JSON string for visualization.
    
    Args:
        result: The extracted entities as a dictionary
    
    Returns:
        JSON string representation of the result
    """
    formatted_json = json.dumps(result, indent=4, ensure_ascii=False, 
                                default=str)
    print("\nExtracted entities:")
    print(formatted_json)


def save_entities(route, json_entities: Dict):
    """
    Save the extracted entities to a JSON file.
    
    Args:
        route (str): The file path where the JSON will be saved
        json_entities (Dict): The extracted entities as a dictionary
    """
    if not route.endswith(".json"):
        raise ValueError("The route must end with '.json'")
    
    # Ensure the directory exists
    os.makedirs(os.path.dirname(route), exist_ok=True)
    
    # Write the JSON data to the specified file

    with open(route, "w", encoding="utf-8") as f:
        json.dump(json_entities, f, ensure_ascii=False, indent=2)


def main():
    """
    Función principal para ejecutar la extracción de conceptos clínicos.
    """
    # 1. Ejemplo de texto clínico para procesar
    sample_text = """
    Paciente de 65 años con antecedentes de Hipertensión Arterial y Diabetes Mellitus tipo 2. 
    Presenta cuadro de disnea de esfuerzo y edemas en miembros inferiores. 
    Se prescribe Enalapril 10mg cada 12 horas y Furosemida 40mg al día.
    """

    print("--- Iniciando Fase 1: Extracción de Conceptos Clínicos ---")
    
    try:
        # 2. Ejecutar la extracción
        # Puedes cambiar 'source' a "openai" (por defecto)
        print(f"Procesando texto...")
        resultado = extract_medical_entities(
            clinical_text=sample_text, 
            source="openai", 
            temperature=0.0
        )

        # 3. Visualizar los resultados en consola
        visual_json(resultado)

        # 4. Guardar los resultados en un archivo local
        output_path = "data/output/extraccion_test.json"
        save_entities(output_path, resultado)
        print(f"\n[OK] Resultados guardados exitosamente en: {output_path}")

    except Exception as e:
        print(f"\n[ERROR] Ocurrió un fallo durante la ejecución: {e}")

if __name__ == "__main__":
    main()