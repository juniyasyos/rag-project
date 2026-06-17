# 🤖 AI Agent RAG Cheat-Sheet

**CRITICAL INSTRUCTION FOR ALL AI AGENTS:** 
DO NOT blindly `grep` or `cat` hundreds of files to understand how a component works in this Laravel project. **Use the `rag-project` CLI.** It saves 99% of your context window and prevents hallucinations.

## 🛠️ Path & Invocation
1. Ensure you are in the Laravel project root (`/home/juni/projects/apps/siimut`).
2. Prefix your command if `rag-project` is not in PATH:
   `/home/juni/projects/apps/siimut/rag-project/.venv/bin/rag-project <command>`

## 🔍 Core Workflows

### 1. How to map relationships (The "Inspect" Command)
If you need to know "Which services use `User`?" or "What policies authorize `ImutData`?":
```bash
# 1. Find the exact node ID first
rag-project graph "User"

# 2. Inspect its full inbound/outbound relations
rag-project inspect "model-user"
```
*Output will show you EXACTLY which controllers, services, policies, routes, and Filament components interact with it.*

### 2. How to understand feature architecture (The "Query" Command)
If you are asked to modify a feature and need broader context (Docs + Code structure):
```bash
rag-project query --intent architecture_analysis --subject "DailyReport"
```

### 3. Has the codebase changed significantly?
If you've just created new files, generated models, or moved classes around, the RAG graph is stale. Rebuild it BEFORE querying:
```bash
rag-project refresh
```

## 🧠 Graph Schema Cheat-Sheet

- **Node IDs:** Usually format is `<type>-<name_lower>`, e.g., `model-user`, `service-dailyreportservice`, `table-users`, `filament-resource-userresource`.
- **Key Edge Types:**
  - `uses_model`: Component (Service, Controller, Command, Job) imports/uses a Model.
  - `depends_on`: Service A injects Service/Repository B in constructor.
  - `authorizes`: Policy authorizes a Model.
  - `creates_table` / `has_column`: Migration definitions.
  - `handled_by`: Route maps to a Controller.
  - `seeds`: Seeder inserts data for a Model.

**Remember: You are paired with a "Caveman Librarian". It gives you structured mapping, YOU do the thinking.**
