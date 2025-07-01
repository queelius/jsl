# Installation

JSL requires Python 3.8 or later. The language is designed to be lightweight with minimal dependencies.

## From Source

Clone the repository and install JSL:

```bash
git clone https://github.com/your-org/jsl.git
cd jsl
pip install -e .
```

## Verify Installation

Test that JSL is working correctly:

```bash
# Run a simple JSL program
echo '["print", "Hello, JSL!"]' | python -m jsl

# Or run interactively
python -m jsl --repl
```

## Dependencies

JSL has minimal dependencies:

- **Python 3.8+** - Core runtime
- **FastAPI** (optional) - For the web service interface
- **uvicorn** (optional) - For running the web service

## Development Setup

For development work:

```bash
# Clone the repository
git clone https://github.com/your-org/jsl.git
cd jsl

# Create a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in development mode with all dependencies
pip install -e ".[dev]"

# Run tests
python -m pytest tests/

# Build documentation
mkdocs serve
```

## Docker

Run JSL in a container:

```bash
# Build the image
docker build -t jsl .

# Run a JSL program
echo '["print", "Hello from Docker!"]' | docker run -i jsl

# Start the web service
docker run -p 8000:8000 jsl --service
```

## Next Steps

- **[Quick Start](quickstart.md)** - Your first JSL program
- **[Basic Examples](examples.md)** - Common patterns and idioms
- **[Language Guide](../language/overview.md)** - Complete language reference
