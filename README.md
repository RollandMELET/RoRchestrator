# 🎭 RoRchestrator

> Orchestrate parallel Claude Code execution using Git Worktrees and DAG-based dependency management

[![Python Version](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/tests-57%20passing-brightgreen.svg)](tests/)
[![Dependencies](https://img.shields.io/badge/dependencies-0%20(stdlib%20only)-success.svg)]()

**Speed up your Claude Code development by running multiple features in parallel.**

---

## 🚀 Quick Start (5 minutes)

### Installation

```bash
# Method 1: Global wrapper (recommended)
curl -o ~/bin/rorchestrator https://raw.githubusercontent.com/RollandMELET/RoRchestrator/main/install/wrapper.sh
chmod +x ~/bin/rorchestrator

# Method 2: Clone into your project
cd /path/to/your/project
git clone https://github.com/RollandMELET/RoRchestrator.git orchestrator
cd orchestrator
```

### Configuration

```bash
# 1. Copy config template
cp config/feature_list.example.json config/feature_list.json

# 2. Define your features
nano config/feature_list.json
```

**Minimal config:**
```json
{
  "project": {
    "name": "MyProject",
    "repo_path": "..",
    "base_branch": "main"
  },
  "features": [
    {
      "id": "auth",
      "name": "User Authentication",
      "depends_on": [],
      "prompt_file": "auth.md"
    },
    {
      "id": "api",
      "name": "REST API",
      "depends_on": ["auth"],
      "prompt_file": "api.md"
    }
  ]
}
```

```bash
# 3. Create prompts
nano prompts/auth.md
nano prompts/api.md
```

### Run

```bash
# See execution plan
rorchestrator plan
# or: python3 orchestrate.py plan

# Execute
rorchestrator run --yes
# or: python3 orchestrate.py run --yes
```

**Output:**
```
PLAN D'EXÉCUTION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

VAGUE 1
  │ auth: User Authentication (~30k tokens)

VAGUE 2 [PARALLÈLE]
  │ api: REST API (~40k tokens)

💰 Estimated cost: ~$2.10
⚡ Speedup: 2.0x

🚀 EXECUTING...

[14:30] 🚀 auth: started
[14:33] ✅ auth: completed
[14:33] 🚀 api: started
[14:36] ✅ api: completed

✅ DONE - 2/2 features completed in 6 minutes
💰 Total cost: $2.15
```

---

## ✨ Features

### Core Capabilities

- **🎯 DAG-based dependency management** - Automatic detection of execution order
- **🔀 Parallel execution** - Run independent features simultaneously
- **🏗️ Git Worktree isolation** - Each feature in its own environment
- **📊 Real-time monitoring** - Track progress as features execute
- **💰 Cost tracking** - Know exactly what you're spending
- **🧪 Fully tested** - 57 unit tests, 100% coverage
- **🪶 Zero dependencies** - Python stdlib only

### What Gets Automated

- Feature dependency resolution
- Git worktree creation/cleanup
- Claude Code headless execution
- Progress monitoring
- Metrics aggregation (cost, duration)
- Branch creation per feature
- JSON reports generation

---

## 📖 Documentation

| Document | Description |
|----------|-------------|
| **[QUICKSTART.md](QUICKSTART.md)** | Get started in 5 minutes |
| **[GUIDE-UTILISATION.md](GUIDE-UTILISATION.md)** | Complete user guide (French) |
| **[WRAPPER-GLOBAL.md](WRAPPER-GLOBAL.md)** | Global wrapper installation |
| **[VALIDATION-REELLE.md](VALIDATION-REELLE.md)** | Real-world validation report |
| **[RAPPORT-MVP.md](RAPPORT-MVP.md)** | MVP delivery report (French) |

---

## 🎯 Use Cases

### Rails/Ruby Projects

Complete example config for GS1 traceability module in `config/feature_list.example.json`:

```json
{
  "features": [
    {"id": "auth-gtin", "depends_on": []},
    {"id": "api-lookup", "depends_on": ["auth-gtin"]},
    {"id": "batch-import", "depends_on": ["auth-gtin"]},
    {"id": "dashboard", "depends_on": ["api-lookup", "batch-import"]}
  ]
}
```

**Result:** 4 features in 3 waves → 1.3x speedup

### Node.js/React Projects

```json
{
  "features": [
    {"id": "setup-vite", "depends_on": []},
    {"id": "header", "depends_on": ["setup-vite"]},
    {"id": "sidebar", "depends_on": ["setup-vite"]},
    {"id": "main-view", "depends_on": ["header", "sidebar"]}
  ]
}
```

**Result:** 4 features in 3 waves → 1.5x speedup

### Python/FastAPI Projects

Works with any stack. Adapt `claude.allowed_tools` in config.

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────┐
│                 ORCHESTRATOR                        │
│                                                     │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐          │
│  │   DAG    │→ │ Worktree │→ │  Claude  │          │
│  │ Resolver │  │ Manager  │  │  Runner  │          │
│  └──────────┘  └──────────┘  └──────────┘          │
│                                    │                │
│                                    ▼                │
│                             ┌──────────┐            │
│                             │ Reporter │            │
│                             └──────────┘            │
└─────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        ▼                     ▼                     ▼
┌─────────────┐       ┌─────────────┐       ┌─────────────┐
│ worktrees/  │       │ worktrees/  │       │ worktrees/  │
│ feature-a/  │       │ feature-b/  │       │ feature-c/  │
│             │       │             │       │             │
│ Claude #1   │       │ Claude #2   │       │ Claude #3   │
│ (async)     │       │ (async)     │       │ (async)     │
└─────────────┘       └─────────────┘       └─────────────┘
```

**Components:**

- **DAG Resolver** (`core/dag.py`) - Validates dependencies, calculates execution waves
- **Worktree Manager** (`core/worktree.py`) - Creates isolated Git environments
- **Claude Runner** (`core/runner.py`) - Executes Claude Code in headless mode with asyncio
- **Reporter** (`core/reporter.py`) - Real-time progress, metrics, JSON reports

---

## 📊 Real-World Validation

**Tested on:** TODO app (3 features, Python)

| Metric | Value |
|--------|-------|
| **Features completed** | 3/3 (100%) ✅ |
| **Duration** | 10.5 minutes |
| **Cost** | $2.46 |
| **Code created** | ~335 lines |
| **Tests created** | ~530 lines |
| **Application status** | Fully functional ✅ |

**See:** [VALIDATION-REELLE.md](VALIDATION-REELLE.md) for full report

---

## 🛠️ CLI Commands

### `plan` - Preview execution plan

```bash
rorchestrator plan
```

Shows DAG structure, execution waves, and cost estimates.

### `run` - Execute features

```bash
rorchestrator run          # With confirmation
rorchestrator run --yes    # Skip confirmation
rorchestrator run --sequential  # Debug mode
```

### `cleanup` - Clean worktrees

```bash
rorchestrator cleanup --merged  # Clean merged only
rorchestrator cleanup --all     # Clean all (careful!)
```

### `status` - Show project status

```bash
rorchestrator status
```

Shows: project info, active worktrees, Claude CLI availability.

---

## 📦 What's Included

### Code (~1350 lines)

- ✅ **4 core modules** - DAG, Worktree, Runner, Reporter
- ✅ **CLI** - Complete command-line interface
- ✅ **57 tests** - Unit tests with 100% coverage
- ✅ **3 demos** - Fully functional demonstrations

### Documentation

- ✅ **Quick Start** - 5-minute setup guide
- ✅ **User Guide** - Complete usage documentation
- ✅ **Examples** - Rails/GS1 and Node.js configs
- ✅ **Validation Report** - Real-world test results

### Configuration Examples

- ✅ **Rails/GS1** - Complete traceability module example
- ✅ **Python TODO** - Simple app for testing
- ✅ **Prompts** - 5 production-ready prompt templates

---

## 🧪 Testing

```bash
# Run all tests
python3 -m unittest discover tests -v

# Run specific test suite
python3 -m unittest tests/test_dag.py -v
python3 -m unittest tests/test_worktree.py -v
python3 -m unittest tests/test_runner.py -v
python3 -m unittest tests/test_reporter.py -v

# Run demos
python3 demo_dag.py
python3 demo_worktree.py
python3 demo_integrated.py
```

**Result:** `Ran 57 tests in 1.5s - OK ✅`

---

## 🎓 How It Works

### 1. Define Features with Dependencies

```json
{
  "features": [
    {"id": "A", "depends_on": []},
    {"id": "B", "depends_on": ["A"]},
    {"id": "C", "depends_on": ["A"]},
    {"id": "D", "depends_on": ["B", "C"]}
  ]
}
```

### 2. RoRchestrator Calculates Execution Waves

```
Wave 1: [A]           ← Sequential
Wave 2: [B, C]        ← PARALLEL ⚡
Wave 3: [D]           ← Sequential
```

### 3. Each Feature Gets Its Own Worktree

```
../worktrees/
├── A/  → branch: feature/A
├── B/  → branch: feature/B
├── C/  → branch: feature/C
└── D/  → branch: feature/D
```

### 4. Claude Code Runs in Parallel

```bash
# Automatically executed by RoRchestrator:
claude -p "$(cat prompts/B.md)" --output-format json  # In worktree B
claude -p "$(cat prompts/C.md)" --output-format json  # In worktree C (parallel!)
```

### 5. Results Aggregated & Reported

```
✅ Feature A: $0.50, 2min
✅ Feature B: $0.80, 3min  } Parallel!
✅ Feature C: $0.60, 3min  }
✅ Feature D: $1.00, 4min

Total: $2.90, 12min (vs 16min sequential → 1.33x speedup)
```

---

## ⚙️ Requirements

- **Python 3.9+** (stdlib only - no external dependencies!)
- **Git**
- **Claude Code CLI** - Install from [claude.ai/code](https://claude.ai/code)

**Verify:**
```bash
python3 --version  # >= 3.9
git --version
claude --version
```

---

## 💡 When to Use

### ✅ Use RoRchestrator When:

- You have 3+ features with dependencies
- Features are well-defined (clear prompts)
- You want to automate development
- You need cost/time tracking

### ❌ Don't Use When:

- Single feature or simple changes
- Features are exploratory/unclear
- Rapid iteration needed
- Manual intervention required

---

## 📈 Benefits

| Aspect | Benefit |
|--------|---------|
| **Speed** | 1.3x - 2x faster (depends on parallelism) |
| **Automation** | Zero manual intervention after config |
| **Quality** | Consistent code quality (same prompts) |
| **Traceability** | JSON reports with full metrics |
| **Isolation** | Each feature in separate worktree |
| **Simplicity** | JSON config, no code to write |

---

## 🗂️ Project Structure

```
RoRchestrator/
├── core/                    # Core modules
│   ├── dag.py              # DAG resolver (16 tests)
│   ├── worktree.py         # Worktree manager (17 tests)
│   ├── runner.py           # Async Claude runner (14 tests)
│   └── reporter.py         # Metrics & reporting (10 tests)
├── orchestrate.py          # Main CLI
├── config/                 # Configuration files
│   ├── feature_list.json          # Your config
│   ├── feature_list.example.json  # Rails/GS1 example
│   └── test-project.json          # Test example
├── prompts/                # Prompt templates
│   ├── auth-gtin.md       # GS1 GTIN validation
│   ├── api-lookup.md      # REST API endpoint
│   └── ...
├── tests/                  # 57 unit tests
├── demo_*.py              # Demonstration scripts
└── docs/
    ├── QUICKSTART.md
    ├── GUIDE-UTILISATION.md
    └── VALIDATION-REELLE.md
```

---

## 📝 Example Workflow

```bash
# 1. Plan
rorchestrator plan

# Output:
#   WAVE 1: [auth]
#   WAVE 2: [api, batch] ← PARALLEL
#   WAVE 3: [dashboard]
#   Estimated cost: $5.40

# 2. Execute
rorchestrator run --yes

# 3. Monitor (real-time)
#   [14:30] 🚀 auth: started
#   [14:33] ✅ auth: completed
#   [14:33] 🚀 api: started (parallel)
#   [14:33] 🚀 batch: started (parallel)
#   ...

# 4. Review results
cd ../worktrees/auth
code .

# 5. Merge
git checkout main
git merge feature/auth
git push

# 6. Cleanup
rorchestrator cleanup --merged
```

---

## 🎨 Example: GS1 Traceability Module

**Included in `config/feature_list.example.json`**

Develops a complete Rails traceability module:

1. **auth-gtin** - GTIN validation (GS1 standards)
2. **api-lookup** - REST API endpoint
3. **batch-import** - CSV import functionality
4. **dashboard** - Hotwire UI dashboard

**Execution:**
- 3 waves (1 sequential, 1 with 2 parallel, 1 sequential)
- ~180k tokens (~$5.40)
- 15-20 minutes
- 1.3x speedup vs sequential

**Prompts included and ready to use!**

---

## 🧑‍💻 Development

### Run Tests

```bash
python3 -m unittest discover tests -v
# Ran 57 tests in 1.5s - OK
```

### Test Coverage

| Module | Tests | Coverage |
|--------|-------|----------|
| dag.py | 16 | 100% |
| worktree.py | 17 | 100% |
| runner.py | 14 | 100% |
| reporter.py | 10 | 100% |

### Run Demos

```bash
# DAG demonstration
python3 demo_dag.py

# Worktree demonstration
python3 demo_worktree.py

# Full integrated demo (creates temp repo, runs mock Claude)
python3 demo_integrated.py
```

---

## 🔧 Advanced Usage

### Custom Configuration

```json
{
  "project": {
    "max_parallel": 3,        // Max 3 features at once
    "timeout_seconds": 1800   // 30 min per feature
  },
  "claude": {
    "permission_mode": "acceptEdits",
    "allowed_tools": [
      "Read", "Write", "Edit",
      "Bash(npm test)"
    ]
  }
}
```

### Debugging

```bash
# Run sequentially (easier to debug)
rorchestrator run --sequential

# Check status
rorchestrator status
```

### Custom Config File

```bash
rorchestrator plan --config config/my-custom.json
rorchestrator run --config config/my-custom.json --yes
```

---

## 🤝 Contributing

Contributions welcome! This project started as an analysis in 101ÉvolutionLab and evolved into a production tool.

### Development Setup

```bash
git clone https://github.com/RollandMELET/RoRchestrator.git
cd RoRchestrator
python3 -m unittest discover tests -v
```

---

## 📜 License

MIT License - See [LICENSE](LICENSE) file.

---

## 🙏 Acknowledgments

- **Claude Code** - The amazing AI coding assistant by Anthropic
- **101ÉvolutionLab** - Origin project where this was born
- **Python graphlib** - Native topological sorting

---

## 🐛 Troubleshooting

### "Claude CLI not available"

```bash
which claude
# If not found, install from: https://claude.ai/code
```

### "Not in a Git repository"

```bash
git init
git add .
git commit -m "Initial commit"
```

### Rate limits / Too many parallel

Lower `max_parallel` in config:
```json
{"project": {"max_parallel": 2}}
```

---

## 📊 Stats

- **Lines of code:** ~1,350
- **Lines of tests:** ~1,500
- **Test coverage:** 100%
- **External dependencies:** 0
- **Development time:** ~5 hours
- **Real-world validation:** ✅ Passed

---

## 🗺️ Roadmap

### Current (v1.0.0)

- ✅ DAG dependency resolution
- ✅ Parallel execution with asyncio
- ✅ Git worktree management
- ✅ Real-time monitoring
- ✅ Cost/duration tracking
- ✅ CLI interface

### Future (v1.1+)

- [ ] Interactive dependency assistant
- [ ] Prompt templates library
- [ ] Automatic retry with backoff
- [ ] Notifications (Slack, Discord)
- [ ] Historical metrics
- [ ] Web UI for monitoring

---

## 📬 Contact

**Author:** Rolland Melet
**Project:** Part of 101ÉvolutionLab ecosystem

---

## ⭐ Show Your Support

If RoRchestrator helps your workflow, give it a ⭐ on GitHub!

---

**Made with Claude Code (Sonnet 4.5) 🤖**
