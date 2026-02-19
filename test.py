import sys
print(f"Python version: {sys.version}")
print(f"Executable: {sys.executable}")

try:
    import fastapi
    print(f"✅ FastAPI version: {fastapi.__version__}")
except ImportError:
    print("❌ FastAPI not found")

try:
    import pydantic
    print(f"✅ Pydantic version: {pydantic.__version__}")
except ImportError:
    print("❌ Pydantic not found")

try:
    import openai
    print(f"✅ OpenAI version: {openai.__version__}")
except ImportError:
    print("❌ OpenAI not found")