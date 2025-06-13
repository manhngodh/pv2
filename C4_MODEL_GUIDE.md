# Passivbot v2.0 - C4 Model Documentation

This document provides C4 model diagrams for the Passivbot v2.0 cryptocurrency trading bot system. The C4 model uses a hierarchical approach to software architecture diagramming, showing the system at different levels of abstraction.

## Overview

The C4 model consists of four levels:
1. **System Context** - How the system fits into the world
2. **Container** - The high-level technology choices and how they communicate
3. **Component** - How containers are made up of components
4. **Code** - How components are implemented (optional)

Additionally, we include:
- **Deployment** - How containers map to infrastructure
- **Dynamic** - How components collaborate for specific scenarios

## Available Formats

This repository contains C4 diagrams in multiple formats to support different tools and workflows:

### 1. Structurizr DSL (`passivbot.dsl`)
**Best for:** Professional documentation, team collaboration, automated diagram generation

**Tools:**
- [Structurizr](https://structurizr.com/) - Official online tool
- [Structurizr CLI](https://github.com/structurizr/cli) - Command-line tool
- [Structurizr Lite](https://structurizr.com/help/lite) - Docker container for local hosting

**Usage:**
```bash
# Using Structurizr CLI
structurizr-cli export -workspace passivbot.dsl -format plantuml

# Using Docker (Structurizr Lite)
docker run -it --rm -p 8080:8080 -v $(pwd):/usr/local/structurizr structurizr/lite
```

### 2. PlantUML C4 (`passivbot_c4.puml`)
**Best for:** Integration with development tools, documentation pipelines

**Tools:**
- [PlantUML](https://plantuml.com/) with C4 extension
- VS Code PlantUML extension
- Confluence, Notion, GitLab, GitHub (with PlantUML support)

**Usage:**
```bash
# Generate PNG diagrams
plantuml -tpng passivbot_c4.puml

# Generate SVG diagrams  
plantuml -tsvg passivbot_c4.puml

# Using Docker
docker run --rm -v $(pwd):/data plantuml/plantuml:latest -tpng /data/passivbot_c4.puml
```

### 3. Mermaid C4 (`C4_ARCHITECTURE.md`)
**Best for:** GitHub/GitLab documentation, quick sharing, web integration

**Tools:**
- GitHub/GitLab (native support)
- [Mermaid Live Editor](https://mermaid.live/)
- VS Code Mermaid extensions
- Notion, Confluence (with Mermaid plugins)

## Diagram Descriptions

### System Context Diagram
Shows Passivbot's place in the broader ecosystem:
- **Users**: Crypto traders who configure and monitor the bot
- **External Systems**: Exchanges (Binance, Bybit), notification services (Telegram, Discord)
- **Main System**: Passivbot v2.0 as a single box

### Container Diagram  
Shows the major containers that make up Passivbot:
- **CLI Application**: Command-line interface for management
- **Web Dashboard**: Real-time monitoring interface
- **Trading Bot Core**: Main trading engine
- **Database**: Persistent storage
- **Configuration**: External config files

### Component Diagram - Trading Bot Core
Detailed view of the main trading engine:
- **Bot Controller**: Main orchestrator
- **Exchange Layer**: Binance/Bybit implementations
- **Strategy Layer**: Grid and DCA strategies
- **Risk Management**: Safety and compliance
- **Data Processing**: Market data and order management

### Deployment Diagram
Shows how the system is deployed:
- **Local Environment**: CLI and configuration files
- **Cloud Server**: Production bot, web dashboard, database
- **External Infrastructure**: Exchange APIs, notification services

### Dynamic Diagrams
Show how components interact for specific scenarios:
- Trading execution flow
- Configuration update process
- Error handling and recovery

## Architecture Principles

### 1. Modular Design
- **Exchange Abstraction**: Easy to add new exchanges
- **Strategy Framework**: Pluggable trading strategies
- **Component Isolation**: Clear boundaries and responsibilities

### 2. Async Architecture
- **Non-blocking I/O**: Concurrent market data processing
- **Event-driven**: Real-time response to market changes
- **Resource Efficient**: Optimal use of system resources

### 3. Reliability & Safety
- **Risk Management**: Built-in safety mechanisms
- **Error Handling**: Comprehensive exception management
- **State Recovery**: Persistent state across restarts

### 4. Observability
- **Structured Logging**: JSON logs for analysis
- **Real-time Monitoring**: Web dashboard with live updates
- **Alerting**: Multi-channel notification system

### 5. Security
- **Credential Management**: Encrypted API key storage
- **Input Validation**: Pydantic models for all data
- **Audit Trail**: Complete activity logging

## Integration with Development Workflow

### 1. Documentation Pipeline
```yaml
# GitHub Actions example
name: Generate Architecture Diagrams
on: [push, pull_request]
jobs:
  diagrams:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Generate PlantUML diagrams
        uses: cloudbees/plantuml-github-action@master
        with:
          args: -tsvg -o docs/diagrams *.puml
```

### 2. VS Code Integration
Recommended extensions:
- PlantUML (jebbs.plantuml)
- Mermaid Preview (bierner.markdown-mermaid)
- C4 DSL (systemticks.c4-dsl-extension)

### 3. Confluence/Notion Integration
- Use PlantUML or Mermaid plugins
- Embed SVG exports for static documentation
- Link to live diagrams for dynamic updates

## Maintenance

### Updating Diagrams
When making architectural changes:

1. **Update the DSL first** (`passivbot.dsl`) - this is the source of truth
2. **Generate other formats** from the DSL when possible
3. **Update component descriptions** to reflect new functionality
4. **Add new relationships** for new integrations
5. **Update deployment info** for infrastructure changes

### Version Control
- Keep diagrams in sync with code changes
- Use semantic versioning for major architectural updates
- Tag diagram versions with corresponding code releases

### Review Process
- Include architecture review in code review process
- Validate diagrams match implementation
- Update documentation for each release

## Tools Comparison

| Tool | Pros | Cons | Best For |
|------|------|------|----------|
| **Structurizr** | Professional, powerful, version control | Paid for teams, learning curve | Enterprise documentation |
| **PlantUML** | Free, widely supported, programmable | Syntax complexity, limited styling | Development integration |
| **Mermaid** | Simple syntax, GitHub native, free | Limited C4 support, fewer features | Quick documentation |

## Examples

### Viewing Diagrams Online

1. **Structurizr DSL**: Copy `passivbot.dsl` content to [Structurizr Express](https://structurizr.com/express)
2. **PlantUML**: Copy individual diagrams to [PlantUML Online Server](http://www.plantuml.com/plantuml/)
3. **Mermaid**: Copy individual diagrams to [Mermaid Live Editor](https://mermaid.live/)

### Local Development Setup

```bash
# Install PlantUML
brew install plantuml  # macOS
sudo apt-get install plantuml  # Ubuntu

# Install Structurizr CLI
wget https://github.com/structurizr/cli/releases/latest/download/structurizr-cli.zip
unzip structurizr-cli.zip

# Generate all diagrams
plantuml -tsvg *.puml
./structurizr.sh export -workspace passivbot.dsl -format plantuml
```

This comprehensive C4 model provides multiple ways to visualize and understand the Passivbot architecture, making it accessible to different stakeholders and development workflows.
