# fuzzy-chainsaw

A short and memorable repository for project development

## Development Setup

This repository is configured for both Python and TypeScript/JavaScript development.

### Python Development

**Requirements:**
- Python 3.11+ (see `.python-version`)
- pip or your preferred package manager

**Setup:**
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Format code
black src tests
isort src tests

# Lint code
ruff check src tests

# Type checking
mypy src
```

**Project Structure:**
- `src/fuzzy_chainsaw/` - Main Python source code
- `tests/` - Python tests
- `pyproject.toml` - Python project configuration

### TypeScript/JavaScript Development

**Requirements:**
- Node.js 20+ (see `.nvmrc`)
- npm or yarn

**Setup:**
```bash
# Install dependencies
npm install

# Build TypeScript
npm run build

# Run tests
npm test

# Run tests in watch mode
npm run test:watch

# Lint code
npm run lint

# Format code
npm run format

# Type check
npm run typecheck
```

**Project Structure:**
- `src/ts/` - TypeScript source code
- `dist/` - Compiled JavaScript output (generated)
- `tsconfig.json` - TypeScript configuration
- `package.json` - Node.js project configuration

## Scripts

### Python
- `pytest` - Run tests with coverage
- `black .` - Format code
- `ruff check .` - Lint code
- `mypy src` - Type checking

### TypeScript
- `npm run build` - Compile TypeScript to JavaScript
- `npm test` - Run Jest tests
- `npm run lint` - Lint with ESLint
- `npm run format` - Format with Prettier

## Contributing

1. Create a feature branch
2. Make your changes
3. Run tests and linting
4. Submit a pull request
