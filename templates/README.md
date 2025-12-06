# Project Templates

Base templates for full-stack project generation using granular sub-questions approach.

## Structure

```
templates/
  frontend/
    react-base/          # Comprehensive React base template
  backend/
    flask-base/         # Comprehensive Flask base template
  database/
    sqlite-base/        # Comprehensive SQLite base template
  integration/
    react-flask/        # React-Flask integration template
```

## Template Design Principles

1. **Comprehensive**: Include all common patterns and structures
2. **Customizable**: Use placeholders ({{PLACEHOLDER}}) for LLM customization
3. **Modular**: Can be combined and extended
4. **Well-documented**: Clear comments and structure

## Usage

Templates are loaded and customized by the granular sub-question system:
- Each sub-question selects a template
- Small LLM calls customize the template
- Results are combined into complete project
