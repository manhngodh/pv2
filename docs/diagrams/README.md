# Passivbot v2.0 - Architecture & Design Diagrams

This folder contains comprehensive visual documentation of the Passivbot trading bot system architecture and design.

## 📁 File Organization

### Core Documentation Files
- **`ARCHITECTURE.md`** - Complete system architecture with all diagrams
- **`QUICK_REFERENCE.md`** - Simplified flowcharts and quick reference
- **`C4_ARCHITECTURE.md`** - C4 model architecture diagrams (Context, Container, Component levels)
- **`C4_MODEL_GUIDE.md`** - Guide for understanding C4 modeling approach

### Interactive Diagrams
- **`diagrams.html`** - Interactive Mermaid diagrams (open in browser)
- **`c4_diagrams.html`** - Interactive C4 model diagrams (open in browser)

### Individual Component Diagrams
- **`01_system_architecture.md`** - High-level system overview
- **`02_bot_lifecycle.md`** - Bot startup, running, and shutdown processes
- **`03_configuration_system.md`** - Configuration loading and validation
- **`04_exchange_layer.md`** - Exchange abstraction and API integration
- **`05_grid_strategy.md`** - Grid trading strategy logic
- **`06_dca_strategy.md`** - Dollar Cost Averaging strategy logic
- **`07_risk_management.md`** - Risk controls and position management
- **`08_data_models.md`** - Core data structures and relationships

### Source Files & Tools
- **`passivbot_c4.puml`** - PlantUML source for C4 diagrams
- **`passivbot.dsl`** - Structurizr DSL source file
- **`generate_diagrams.sh`** - Script to regenerate diagrams from source

## 🎯 Quick Start

### For Visual Learners
1. Open `diagrams.html` in your browser for interactive exploration
2. Read `QUICK_REFERENCE.md` for simplified flowcharts
3. Check individual component files (01-08) for specific details

### For Architects & Developers
1. Review `C4_ARCHITECTURE.md` for structured architecture views
2. Use `ARCHITECTURE.md` for comprehensive technical details
3. Modify source files (`*.puml`, `*.dsl`) and run `generate_diagrams.sh` to update

### For New Contributors
1. Start with `01_system_architecture.md` for overview
2. Follow the numbered sequence (02-08) for detailed understanding
3. Reference `C4_MODEL_GUIDE.md` for architecture methodology

## 🔧 Diagram Types Explained

### Mermaid Diagrams
- **Flowcharts**: Process flows and decision trees
- **Sequence Diagrams**: Interaction timelines between components
- **Class Diagrams**: Object-oriented structure
- **State Diagrams**: System state transitions

### C4 Model Diagrams
- **Context**: System in its environment
- **Container**: High-level technology choices
- **Component**: Internal structure of containers
- **Code**: Class-level details (when needed)

## 🚀 Usage Examples

### Viewing Interactive Diagrams
```bash
# Open in browser
xdg-open diagrams.html
xdg-open c4_diagrams.html
```

### Regenerating Diagrams
```bash
# Make the script executable
chmod +x generate_diagrams.sh

# Run the generation script
./generate_diagrams.sh
```

### Customizing Diagrams
1. Edit source files (`.puml`, `.dsl`, or `.md` files)
2. Run generation script if using PlantUML/Structurizr
3. For Mermaid diagrams, edit directly in markdown files

## 📋 Diagram Coverage

### System Level
- [x] Overall architecture
- [x] External integrations
- [x] Data flow
- [x] Deployment view

### Component Level
- [x] Core bot engine
- [x] Exchange abstraction
- [x] Strategy framework
- [x] Configuration system
- [x] Risk management
- [x] CLI interface

### Process Level
- [x] Bot lifecycle
- [x] Strategy execution
- [x] Order management
- [x] Error handling
- [x] Risk controls

### Data Level
- [x] Core data models
- [x] Configuration schemas
- [x] API request/response
- [x] Database entities

## 🔄 Maintenance

### Updating Diagrams
- When code changes, update corresponding diagrams
- Keep C4 model synchronized with actual architecture
- Validate Mermaid syntax before committing
- Test interactive HTML files in browsers

### Review Process
1. Technical accuracy review
2. Visual clarity assessment
3. Consistency check across diagrams
4. Browser compatibility testing

## 🎨 Diagram Standards

### Naming Conventions
- Use clear, descriptive names
- Follow existing color schemes
- Maintain consistent styling
- Use standard UML/C4 conventions

### File Naming
- `##_descriptive_name.md` for numbered sequence
- `UPPERCASE.md` for main documentation
- `lowercase.html` for interactive versions
- `source.ext` for editable source files

---

**Note**: All diagrams are living documents that should evolve with the codebase. Keep them updated as the system grows and changes.
