# Multi-Language Static Analyzer 🌍

## Supports ALL Major Languages!

The static analyzer now works for **TypeScript, JavaScript, Go, Java, Python, and more!**

## Supported Languages

✅ **TypeScript** (.ts, .tsx)
✅ **JavaScript** (.js, .jsx)
✅ **Python** (.py)
✅ **Go** (.go)
✅ **Java** (.java)
✅ **Rust** (.rs)
✅ **Ruby** (.rb)
✅ **PHP** (.php)
✅ **C#** (.cs)
✅ **C++** (.cpp)
✅ **C** (.c)

## Usage

### Command Line

```bash
# Analyze any language file
python -m llmobserve.multi_language_analyzer my_agent.ts
python -m llmobserve.multi_language_analyzer my_agent.js
python -m llmobserve.multi_language_analyzer my_agent.go
```

### Python API

```python
from llmobserve.multi_language_analyzer import preview_multi_language_tree

# TypeScript
typescript_code = """
export async function researchAgent(query: string) {
    const results = await webSearchTool(query);
    return results;
}
"""
preview = preview_multi_language_tree(code=typescript_code, language="typescript")
print(preview)

# JavaScript
javascript_code = """
async function researchAgent(query) {
    const results = await webSearchTool(query);
    return results;
}
"""
preview = preview_multi_language_tree(code=javascript_code, language="javascript")
print(preview)

# Go
go_code = """
func researchAgent(query string) string {
    results := webSearchTool(query)
    return results
}
"""
preview = preview_multi_language_tree(code=go_code, language="go")
print(preview)
```

## How It Works

### Language Detection

Automatically detects language from file extension:
- `.ts`, `.tsx` → TypeScript
- `.js`, `.jsx` → JavaScript
- `.py` → Python
- `.go` → Go
- `.java` → Java
- etc.

### Pattern Matching

Uses regex patterns to detect:
- **Agents**: `*agent*`, `*orchestrat*`, `*workflow*`, `*pipeline*`
- **Tools**: `*tool*`, `*function*`, `*call*`
- **Steps**: `*step*`, `*stage*`, `*task*`

### API Call Detection

Detects API calls per language:
- **TypeScript/JavaScript**: `fetch()`, `axios.get()`, `client.chat.completions.create()`
- **Python**: `requests.get()`, `client.chat.completions.create()`
- **Go**: `http.Get()`, `client.Do()`
- **Java**: `HttpClient.get()`, `.execute()`

## Examples

### TypeScript

```typescript
export async function researchAgent(query: string): Promise<string> {
    const results = await webSearchTool(query);
    return results;
}

async function webSearchTool(query: string): Promise<string> {
    const response = await fetch(`https://api.example.com/search?q=${query}`);
    return await response.text();
}
```

**Detected:**
- `agent:research` (researchAgent)
- `tool:webSearch` (webSearchTool)
- API call: `fetch()`

### JavaScript

```javascript
async function researchAgent(query) {
    const results = await webSearchTool(query);
    const analysis = await analyzeTool(results);
    return analysis;
}

async function webSearchTool(query) {
    const response = await fetch(`https://api.example.com/search?q=${query}`);
    return await response.text();
}

async function analyzeTool(data) {
    const response = await axios.post('https://api.example.com/analyze', { data });
    return response.data;
}
```

**Detected:**
- `agent:research` (researchAgent)
- `tool:webSearch` (webSearchTool)
- `tool:analyze` (analyzeTool)
- API calls: `fetch()`, `axios.post()`

### Go

```go
func researchAgent(query string) string {
    results := webSearchTool(query)
    return results
}

func webSearchTool(query string) string {
    resp, _ := http.Get("https://api.example.com/search?q=" + query)
    return resp.Body
}
```

**Detected:**
- `agent:research` (researchAgent)
- `tool:webSearch` (webSearchTool)
- API call: `http.Get()`

### Java

```java
public class ResearchAgent {
    public String researchAgent(String query) {
        String results = webSearchTool(query);
        return results;
    }
    
    private String webSearchTool(String query) {
        // HTTP call
        return "results";
    }
}
```

**Detected:**
- `agent:research` (researchAgent)
- `tool:webSearch` (webSearchTool)

## Features

✅ **Multi-language support** - Works with TypeScript, JavaScript, Go, Java, Python, and more
✅ **Automatic language detection** - Detects from file extension
✅ **Pattern matching** - Detects agents/tools/steps across languages
✅ **API call detection** - Language-specific API patterns
✅ **Call graph building** - Tracks function call relationships
✅ **Tree visualization** - Shows hierarchical structure

## Limitations

⚠️ **Regex-based** - Uses regex patterns (not full parsers)
⚠️ **Pattern matching** - May have false positives/negatives
⚠️ **No semantic analysis** - Can't understand code meaning
⚠️ **Static only** - Can't detect dynamic calls

But it's **good enough** for previewing agent structure across languages!

## Summary

**Multi-language static analyzer:**
- ✅ Works with TypeScript, JavaScript, Go, Java, Python, and more
- ✅ Automatic language detection
- ✅ Pattern-based agent/tool/step detection
- ✅ Language-specific API call detection
- ✅ Tree visualization for any language

**Perfect for:**
- TypeScript/JavaScript APIs (most common!)
- Go microservices
- Java applications
- Python scripts
- Any language with function-like structures

