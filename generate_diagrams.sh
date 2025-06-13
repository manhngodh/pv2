#!/bin/bash

# Passivbot C4 Diagram Generator
# This script helps generate C4 diagrams in various formats

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to generate PlantUML diagrams
generate_plantuml() {
    if command_exists plantuml; then
        print_status "Generating PlantUML diagrams..."
        
        # Create output directory
        mkdir -p diagrams/plantuml
        
        # Generate PNG diagrams
        plantuml -tpng -o diagrams/plantuml passivbot_c4.puml
        
        # Generate SVG diagrams
        plantuml -tsvg -o diagrams/plantuml passivbot_c4.puml
        
        print_success "PlantUML diagrams generated in diagrams/plantuml/"
    else
        print_warning "PlantUML not found. Install with: brew install plantuml (macOS) or sudo apt-get install plantuml (Ubuntu)"
    fi
}

# Function to generate diagrams using Docker
generate_with_docker() {
    if command_exists docker; then
        print_status "Generating diagrams using Docker..."
        
        # Create output directory
        mkdir -p diagrams/docker
        
        # Generate PlantUML diagrams with Docker
        docker run --rm -v "$(pwd):/data" plantuml/plantuml:latest -tpng -o /data/diagrams/docker /data/passivbot_c4.puml
        docker run --rm -v "$(pwd):/data" plantuml/plantuml:latest -tsvg -o /data/diagrams/docker /data/passivbot_c4.puml
        
        print_success "Docker-generated diagrams saved in diagrams/docker/"
    else
        print_warning "Docker not found. Install Docker to use this option."
    fi
}

# Function to start Structurizr Lite
start_structurizr() {
    if command_exists docker; then
        print_status "Starting Structurizr Lite on http://localhost:8080"
        print_status "Upload the passivbot.dsl file in the web interface"
        
        docker run -it --rm -p 8080:8080 -v "$(pwd):/usr/local/structurizr" structurizr/lite
    else
        print_warning "Docker not found. Install Docker to use Structurizr Lite."
    fi
}

# Function to validate DSL syntax
validate_dsl() {
    if [ -f "passivbot.dsl" ]; then
        print_status "Validating Structurizr DSL syntax..."
        
        # Basic syntax check (look for common issues)
        if grep -q "workspace" passivbot.dsl && grep -q "model" passivbot.dsl && grep -q "views" passivbot.dsl; then
            print_success "DSL syntax appears valid"
        else
            print_error "DSL syntax may have issues - missing required sections"
        fi
    else
        print_error "passivbot.dsl not found"
    fi
}

# Function to create HTML preview
create_html_preview() {
    print_status "Creating HTML preview file..."
    
    cat > diagrams_preview.html << 'EOF'
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Passivbot C4 Architecture Diagrams</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; }
        h1, h2 { color: #333; }
        .diagram-section { margin: 30px 0; padding: 20px; border: 1px solid #ddd; border-radius: 5px; }
        .diagram-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; }
        .diagram-item { text-align: center; }
        .diagram-item img { max-width: 100%; height: auto; border: 1px solid #ddd; border-radius: 5px; }
        .tabs { display: flex; margin-bottom: 20px; }
        .tab { padding: 10px 20px; background: #f0f0f0; border: 1px solid #ddd; cursor: pointer; }
        .tab.active { background: #007acc; color: white; }
        .tab-content { display: none; }
        .tab-content.active { display: block; }
        .mermaid { text-align: center; }
        .code-block { background: #f8f8f8; padding: 15px; border-radius: 5px; overflow-x: auto; }
        .tools-section { background: #e8f4f8; padding: 15px; border-radius: 5px; margin: 20px 0; }
    </style>
    <script src="https://cdn.jsdelivr.net/npm/mermaid/dist/mermaid.min.js"></script>
</head>
<body>
    <div class="container">
        <h1>🤖 Passivbot v2.0 - C4 Architecture Diagrams</h1>
        
        <div class="tools-section">
            <h3>🛠️ Available Tools & Formats</h3>
            <ul>
                <li><strong>Structurizr DSL:</strong> <code>passivbot.dsl</code> - Professional tool, upload to <a href="https://structurizr.com/express" target="_blank">Structurizr Express</a></li>
                <li><strong>PlantUML:</strong> <code>passivbot_c4.puml</code> - Generate with PlantUML or view at <a href="http://www.plantuml.com/plantuml/" target="_blank">PlantUML Server</a></li>
                <li><strong>Mermaid:</strong> Below diagrams - GitHub native, edit at <a href="https://mermaid.live/" target="_blank">Mermaid Live</a></li>
            </ul>
        </div>

        <div class="tabs">
            <div class="tab active" onclick="showTab('context')">System Context</div>
            <div class="tab" onclick="showTab('container')">Containers</div>
            <div class="tab" onclick="showTab('component')">Components</div>
            <div class="tab" onclick="showTab('deployment')">Deployment</div>
            <div class="tab" onclick="showTab('dynamic')">Dynamic Flow</div>
        </div>

        <div id="context" class="tab-content active">
            <h2>🌐 System Context Diagram</h2>
            <p>Shows how Passivbot fits into the overall environment and interacts with external systems.</p>
            <div class="mermaid">
                C4Context
                title System Context - Passivbot Trading Bot
                Person(trader, "Crypto Trader", "Configures and monitors trading")
                System(passivbot, "Passivbot v2.0", "Automated cryptocurrency trading bot")
                System_Ext(binance, "Binance", "Crypto exchange")
                System_Ext(bybit, "Bybit", "Crypto exchange")
                System_Ext(telegram, "Telegram", "Notifications")
                System_Ext(discord, "Discord", "Notifications")
                Rel(trader, passivbot, "Configures & monitors")
                Rel(passivbot, binance, "Trading API")
                Rel(passivbot, bybit, "Trading API")
                Rel(passivbot, telegram, "Alerts")
                Rel(passivbot, discord, "Alerts")
            </div>
        </div>

        <div id="container" class="tab-content">
            <h2>📦 Container Diagram</h2>
            <p>Shows the major containers that make up the Passivbot system.</p>
            <div class="mermaid">
                C4Container
                title Container Diagram - Passivbot v2.0
                Person(trader, "Trader")
                System_Boundary(c1, "Passivbot System") {
                    Container(cli, "CLI App", "Python/Typer", "Command interface")
                    Container(web, "Web Dashboard", "FastAPI/React", "Monitoring UI")
                    Container(bot, "Trading Bot", "Python/AsyncIO", "Core engine")
                    Container(db, "Database", "PostgreSQL", "Data storage")
                }
                System_Ext(exchanges, "Exchanges")
                Rel(trader, cli, "Commands")
                Rel(trader, web, "Monitor")
                Rel(cli, bot, "Control")
                Rel(web, bot, "Status")
                Rel(bot, db, "Data")
                Rel(bot, exchanges, "Trading")
            </div>
        </div>

        <div id="component" class="tab-content">
            <h2>🔧 Component Diagram</h2>
            <p>Shows the internal components of the Trading Bot Core container.</p>
            <div class="mermaid">
                C4Component
                title Component Diagram - Trading Bot Core
                Container_Boundary(c1, "Trading Bot Core") {
                    Component(controller, "Bot Controller", "Main orchestrator")
                    Component(exchange_mgr, "Exchange Manager", "API abstraction")
                    Component(strategy_mgr, "Strategy Manager", "Trading logic")
                    Component(risk_mgr, "Risk Manager", "Safety controls")
                    Component(order_mgr, "Order Manager", "Order lifecycle")
                }
                System_Ext(exchanges, "Exchanges")
                Rel(controller, exchange_mgr, "Manage")
                Rel(controller, strategy_mgr, "Execute")
                Rel(strategy_mgr, risk_mgr, "Validate")
                Rel(strategy_mgr, order_mgr, "Orders")
                Rel(exchange_mgr, exchanges, "API")
            </div>
        </div>

        <div id="deployment" class="tab-content">
            <h2>🚀 Deployment Diagram</h2>
            <p>Shows how Passivbot is deployed across different environments.</p>
            <div class="mermaid">
                C4Deployment
                title Deployment - Passivbot v2.0
                Deployment_Node(local, "Local Machine") {
                    Container(cli_local, "CLI", "Development")
                }
                Deployment_Node(cloud, "Cloud Server") {
                    Container(bot_prod, "Bot Service", "Production")
                    Container(web_prod, "Web UI", "Monitoring")
                    Container(db_prod, "Database", "PostgreSQL")
                }
                Deployment_Node(exchanges_infra, "Exchange APIs") {
                    Container(apis, "Trading APIs", "External")
                }
                Rel(cli_local, bot_prod, "Deploy")
                Rel(bot_prod, db_prod, "Store")
                Rel(bot_prod, apis, "Trade")
            </div>
        </div>

        <div id="dynamic" class="tab-content">
            <h2>🔄 Dynamic Flow</h2>
            <p>Shows the flow of a typical trading operation.</p>
            <div class="mermaid">
                sequenceDiagram
                    participant MD as Market Data
                    participant SM as Strategy Manager
                    participant RM as Risk Manager
                    participant OM as Order Manager
                    participant EX as Exchange
                    
                    MD->>SM: Price update
                    SM->>SM: Calculate signals
                    SM->>RM: Check risk limits
                    RM-->>SM: Risk approved
                    SM->>OM: Place order
                    OM->>EX: Submit order
                    EX-->>OM: Order confirmation
                    OM->>SM: Order filled
                    SM->>MD: Update positions
            </div>
        </div>

        <div class="diagram-section">
            <h2>📋 Quick Reference</h2>
            <div class="code-block">
                <h4>Generate diagrams locally:</h4>
                <pre>
# PlantUML
plantuml -tsvg passivbot_c4.puml

# Docker PlantUML
docker run --rm -v $(pwd):/data plantuml/plantuml:latest -tsvg /data/passivbot_c4.puml

# Structurizr Lite
docker run -it --rm -p 8080:8080 -v $(pwd):/usr/local/structurizr structurizr/lite
                </pre>
            </div>
        </div>
    </div>

    <script>
        // Initialize Mermaid
        mermaid.initialize({ 
            startOnLoad: true,
            theme: 'default',
            C4: {
                theme: 'default'
            }
        });

        // Tab functionality
        function showTab(tabName) {
            // Hide all tab contents
            const contents = document.getElementsByClassName('tab-content');
            for (let i = 0; i < contents.length; i++) {
                contents[i].classList.remove('active');
            }
            
            // Remove active class from all tabs
            const tabs = document.getElementsByClassName('tab');
            for (let i = 0; i < tabs.length; i++) {
                tabs[i].classList.remove('active');
            }
            
            // Show selected tab content
            document.getElementById(tabName).classList.add('active');
            
            // Add active class to clicked tab
            event.target.classList.add('active');
        }
    </script>
</body>
</html>
EOF

    print_success "HTML preview created: diagrams_preview.html"
}

# Function to show usage
show_usage() {
    echo "Passivbot C4 Diagram Generator"
    echo ""
    echo "Usage: $0 [command]"
    echo ""
    echo "Commands:"
    echo "  plantuml     Generate diagrams using local PlantUML"
    echo "  docker       Generate diagrams using Docker"
    echo "  structurizr  Start Structurizr Lite server"
    echo "  validate     Validate DSL syntax"
    echo "  preview      Create HTML preview"
    echo "  all          Generate all formats and create preview"
    echo "  help         Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 plantuml    # Generate PNG and SVG with PlantUML"
    echo "  $0 docker      # Generate using Docker containers"
    echo "  $0 all         # Generate everything"
}

# Main script logic
case "${1:-help}" in
    plantuml)
        generate_plantuml
        ;;
    docker)
        generate_with_docker
        ;;
    structurizr)
        start_structurizr
        ;;
    validate)
        validate_dsl
        ;;
    preview)
        create_html_preview
        ;;
    all)
        validate_dsl
        generate_plantuml
        generate_with_docker
        create_html_preview
        print_success "All diagrams generated! Open diagrams_preview.html to view."
        ;;
    help|--help|-h)
        show_usage
        ;;
    *)
        print_error "Unknown command: $1"
        show_usage
        exit 1
        ;;
esac
