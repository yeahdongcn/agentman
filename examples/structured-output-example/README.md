# Structured Output Example

This example demonstrates the new structured data output support in Agentman using JSONSchema validation.

## Features

- **Inline JSONSchema as YAML**: Define validation schemas directly in your Agentfile
- **External Schema Files**: Reference separate `.json` or `.yaml` schema files
- **Both Format Support**: Works with both Dockerfile-style and YAML Agentfiles

## Examples

### YAML Format (`Agentfile.yml`)

```yaml
agents:
  - name: sentiment_analyzer
    instruction: Analyze sentiment and return structured results
    output_format:
      type: json_schema
      schema:
        type: object
        properties:
          sentiment:
            type: string
            enum: [positive, negative, neutral]
          confidence:
            type: number
            minimum: 0
            maximum: 1
        required: [sentiment, confidence]

  - name: data_extractor  
    instruction: Extract data from documents
    output_format:
      type: schema_file
      file: ./schemas/extraction_schema.yaml
```

### Dockerfile Format (`Agentfile`)

```dockerfile
AGENT sentiment_analyzer
INSTRUCTION Analyze sentiment and return structured results
OUTPUT_FORMAT json_schema {"type":"object","properties":{"sentiment":{"type":"string","enum":["positive","negative","neutral"]}}}

AGENT file_processor
INSTRUCTION Process files according to schema
OUTPUT_FORMAT schema_file ./schemas/simple_schema.json
```

## Schema Files

### YAML Schema (`schemas/extraction_schema.yaml`)
```yaml
type: object
properties:
  title:
    type: string
  content:
    type: object
    properties:
      paragraphs:
        type: array
        items:
          type: string
required: [title, content]
```

### JSON Schema (`schemas/simple_schema.json`)
```json
{
  "type": "object",
  "properties": {
    "status": {
      "type": "string",
      "enum": ["success", "error"]
    },
    "message": {
      "type": "string"
    }
  },
  "required": ["status", "message"]
}
```

## Usage

1. **Build the agent:**
   ```bash
   agentman build .
   ```

2. **Run with YAML format:**
   ```bash
   agentman run --from-agentfile -f Agentfile.yml .
   ```

3. **Run with Dockerfile format:**
   ```bash
   agentman run --from-agentfile -f Agentfile .
   ```

## Benefits

- **Type Safety**: Validate agent outputs against predefined schemas
- **Documentation**: Schemas serve as output documentation
- **IDE Support**: JSON Schema provides autocomplete and validation in IDEs
- **Flexibility**: Support both inline and external schema definitions
- **Standards**: Uses standard JSONSchema specification