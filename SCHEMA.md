# K-2 Command Center — Data Schema

## Architecture
- **Code:** `RyanSandoval/k2-dashboard` (PUBLIC) — HTML shell only, ZERO data
- **Data:** `RyanSandoval/k2-data` (PRIVATE) — `data.json` via GitHub Contents API
- **⚠️ NEVER put personal data in the public repo**

## Data Schema

All fields marked with `?` are optional but **must be handled as possibly null/undefined in code**.

### Project
```json
{
  "id": "string",           // kebab-case unique ID
  "name": "string",
  "status": "idea|planning|active|review|done",
  "description": "string",
  "goal": "string?",        // Definition of done — what success looks like
  "tags": ["string"]?,      // Can be null/missing — ALWAYS use (p.tags||[])
  "started": "YYYY-MM-DD",
  "nextSteps": [             // Can be null/missing — ALWAYS use (p.nextSteps||[])
    {
      "text": "string",
      "priority": "high|medium|low"
    }
  ]?,
  "notes": [                 // Can be null/missing — ALWAYS use (p.notes||[])
    {
      "text": "string",
      "date": "YYYY-MM-DD",
      "author": "string"
    }
  ]?,
  "links": [
    { "label": "string", "path": "string" }
  ]?
}
```

### Task
```json
{
  "id": "number",
  "text": "string",
  "priority": "high|medium|low",
  "project": "string?",     // project.id reference
  "done": "boolean",
  "created": "YYYY-MM-DD",
  "messages": []?
}
```

### Discussion
```json
{
  "id": "string",
  "title": "string",
  "date": "YYYY-MM-DD",
  "project": "string?",
  "summary": "string",
  "keyPoints": ["string"]?,      // ALWAYS use (d.keyPoints||[])
  "openQuestions": ["string"]?   // ALWAYS use (d.openQuestions||[])
}
```

### Decision
```json
{
  "date": "YYYY-MM-DD",
  "decision": "string",
  "rationale": "string",
  "project": "string?"
}
```

### Note
```json
{
  "text": "string",
  "created": "YYYY-MM-DD HH:MM"
}
```

### Jot Day
```json
{
  "date": "YYYY-MM-DD",
  "entries": [
    {
      "id": "number",
      "text": "string",
      "time": "HH:MM",
      "tags": ["string"],
      "done": "boolean",
      "images": ["base64-data-url"]?,
      "files": [{ "name": "string", "type": "mime", "data": "base64-data-url" }]?
    }
  ]
}
```

### Timeline Event
```json
{
  "date": "YYYY-MM-DD HH:MM",
  "event": "string",
  "project": "string?"
}
```

## CRITICAL RULES

1. **All array fields can be null/undefined** — always use `(field||[])` in JS
2. **nextSteps items are objects** `{text, priority}`, NOT plain strings
3. **Never commit data.json to k2-dashboard** — .gitignore blocks it but be vigilant
4. **When creating projects via API**, include ALL required fields with defaults:
   ```json
   {
     "id": "kebab-case-id",
     "name": "Name",
     "status": "idea",
     "description": "...",
     "goal": "",
     "tags": [],
     "started": "YYYY-MM-DD",
     "nextSteps": [],
     "notes": [],
     "links": []
   }
   ```
5. **Kanban column IDs:** idea, planning, active, review, done

## How to Add Data via CLI

```bash
# Read current data
gh api repos/RyanSandoval/k2-data/contents/data.json --jq '.content' | base64 -d > /tmp/k2-data.json

# Edit /tmp/k2-data.json ...

# Write back
SHA=$(gh api repos/RyanSandoval/k2-data/contents/data.json --jq '.sha')
CONTENT=$(base64 -i /tmp/k2-data.json)
gh api repos/RyanSandoval/k2-data/contents/data.json -X PUT \
  -f message="Update" -f content="$CONTENT" -f sha="$SHA"
```
