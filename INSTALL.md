# Installation Guide - RoRchestrator

Complete installation instructions for all platforms.

---

## Prerequisites

### Required

- **Python 3.9+** - Check with: `python3 --version`
- **Git** - Check with: `git --version`
- **Claude Code CLI** - Install from [claude.ai/code](https://claude.ai/code)

### Verify Setup

```bash
python3 --version
# Python 3.9.0 or higher ✅

git --version
# git version 2.x.x ✅

claude --version
# Claude Code 2.0.x ✅
```

---

## Installation Methods

### Method 1: Global Wrapper (Recommended)

This installs a `rorchestrator` command available everywhere.

#### macOS / Linux

```bash
# 1. Download wrapper script
curl -o ~/bin/rorchestrator https://raw.githubusercontent.com/rollandmelet/rorchestrator/main/install/wrapper.sh

# 2. Make executable
chmod +x ~/bin/rorchestrator

# 3. Add to PATH (if not already)
echo 'export PATH="$HOME/bin:$PATH"' >> ~/.zshrc   # macOS (zsh)
# or
echo 'export PATH="$HOME/bin:$PATH"' >> ~/.bashrc  # Linux (bash)

# 4. Reload shell
source ~/.zshrc  # or ~/.bashrc

# 5. Verify
which rorchestrator
# /Users/YOUR_USERNAME/bin/rorchestrator ✅
```

#### Windows (WSL)

Same as Linux instructions above using WSL terminal.

---

### Method 2: Manual Installation

Install RoRchestrator directly in your project.

```bash
# 1. Go to your project
cd /path/to/your/project

# 2. Clone RoRchestrator
git clone https://github.com/rollandmelet/rorchestrator.git orchestrator

# 3. Verify
cd orchestrator
python3 orchestrate.py --help
```

---

### Method 3: Download ZIP

```bash
# 1. Download
curl -L https://github.com/rollandmelet/rorchestrator/archive/main.zip -o rorchestrator.zip

# 2. Extract
unzip rorchestrator.zip

# 3. Move to your project
mv rorchestrator-main /path/to/your/project/orchestrator

# 4. Verify
cd /path/to/your/project/orchestrator
python3 orchestrate.py --help
```

---

## Post-Installation

### 1. Verify Installation

```bash
# If using global wrapper
rorchestrator --help

# If using local installation
python3 orchestrate.py --help
```

**Expected output:**
```
RoRchestrator - Orchestration parallèle de Claude Code

positional arguments:
  {plan,run,cleanup,status}
    plan                Afficher le plan d'exécution sans exécuter
    run                 Exécuter les features en parallèle
    ...
```

### 2. Run Tests

```bash
cd /path/to/RoRchestrator  # or orchestrator/

python3 -m unittest discover tests -v
```

**Expected:** `Ran 57 tests in 1.5s - OK`

### 3. Run Demo

```bash
python3 demo_integrated.py
```

This creates a temporary Git repo and demonstrates the full workflow with mock Claude execution.

---

## Configuration

### First Project Setup

```bash
# 1. Go to your project (must be Git repo)
cd /path/to/your/project

# 2. If using wrapper
rorchestrator plan
# → Auto-installs RoRchestrator in orchestrator/

# 3. Configure
cd orchestrator
cp config/feature_list.example.json config/feature_list.json
nano config/feature_list.json
```

**Edit:**
- `project.name`: Your project name
- `project.repo_path`: Path to Git repo (usually `..`)
- `project.base_branch`: Your main branch (`main`, `master`, `develop`)
- `features`: Your features list

```bash
# 4. Create prompts
mkdir -p prompts/my-module
nano prompts/my-module/feature-1.md
```

### Prompt Template

```markdown
# Feature: Feature Name

## Objective
What this feature should do.

## Specifications
- Spec 1
- Spec 2

## Success Criteria
- [ ] Tests pass
- [ ] Code works
- [ ] Documentation complete
```

---

## Updating

### Update Global Wrapper

```bash
# Re-download wrapper script
curl -o ~/bin/rorchestrator https://raw.githubusercontent.com/rollandmelet/rorchestrator/main/install/wrapper.sh
chmod +x ~/bin/rorchestrator
```

New projects will get the latest version automatically.

### Update Existing Project

```bash
cd /your/project

# Backup config
cp orchestrator/config/feature_list.json /tmp/backup.json

# Remove old version
rm -rf orchestrator

# Reinstall
rorchestrator plan

# Restore config
cp /tmp/backup.json orchestrator/config/feature_list.json
```

---

## Uninstallation

### Remove Global Wrapper

```bash
rm ~/bin/rorchestrator

# Remove from PATH (edit ~/.zshrc or ~/.bashrc)
nano ~/.zshrc
# Remove the line: export PATH="$HOME/bin:$PATH"
```

### Remove from Project

```bash
cd /your/project
rm -rf orchestrator
```

---

## Troubleshooting

### Python Version Too Old

```bash
python3 --version
# If < 3.9, upgrade Python

# macOS (Homebrew)
brew install python@3.12

# Linux (apt)
sudo apt update && sudo apt install python3.12
```

### Claude Code Not Found

```bash
which claude
# If not found, install from: https://claude.ai/code

# Verify after install
claude --version
```

### Permission Denied

```bash
chmod +x ~/bin/rorchestrator
# or
chmod +x orchestrate.py
```

### Import Errors

Make sure you're in the RoRchestrator directory:

```bash
cd orchestrator  # or RoRchestrator/
python3 orchestrate.py plan
```

---

## Platform-Specific Notes

### macOS

- Use Homebrew for Python: `brew install python@3.12`
- Default shell is zsh: Edit `~/.zshrc`
- PATH already includes `/usr/local/bin`

### Linux

- Python usually pre-installed
- Default shell is bash: Edit `~/.bashrc`
- May need `sudo` for global installations

### Windows (WSL)

- Install WSL2 first
- Follow Linux instructions
- Git must be installed in WSL, not Windows

---

## Support

### Documentation

- **Quick Start**: [QUICKSTART.md](QUICKSTART.md)
- **User Guide**: [GUIDE-UTILISATION.md](GUIDE-UTILISATION.md)
- **Wrapper Guide**: [WRAPPER-GLOBAL.md](WRAPPER-GLOBAL.md)

### Issues

If you encounter problems:
1. Check troubleshooting section above
2. Run demos to verify installation
3. Check that all prerequisites are met
4. Create an issue on GitHub

---

## Next Steps

After installation:

1. **Read**: [QUICKSTART.md](QUICKSTART.md) for 5-minute start
2. **Configure**: Your first `feature_list.json`
3. **Test**: Run `rorchestrator plan` on a small project
4. **Execute**: Try with 2-3 simple features first

---

**Installation complete! Ready to orchestrate. 🎭**
