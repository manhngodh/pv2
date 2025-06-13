workspace "Passivbot v2.0" "Cryptocurrency Trading Bot System Architecture" {

    model {
        # People
        trader = person "Crypto Trader" "User who configures and monitors the automated trading bot to execute grid and DCA strategies"

        # External Systems
        binanceExchange = softwareSystem "Binance Exchange" "Cryptocurrency exchange providing REST API and WebSocket feeds for trading operations" "External"
        bybitExchange = softwareSystem "Bybit Exchange" "Cryptocurrency exchange providing REST API and WebSocket feeds for trading operations" "External"
        telegramService = softwareSystem "Telegram" "Messaging service for sending trading notifications and alerts" "External"
        discordService = softwareSystem "Discord" "Communication platform for sending trading notifications via webhooks" "External"

        # Main System
        passivbotSystem = softwareSystem "Passivbot v2.0" "Modular cryptocurrency trading bot with automated grid and DCA strategies" {
            
            # Containers
            cliApp = container "CLI Application" "Command-line interface for bot management and configuration" "Python, Typer" {
                cliController = component "CLI Controller" "Handles command-line operations and user interactions" "Typer Commands"
                configValidator = component "Config Validator" "Validates configuration files and parameters" "Pydantic Models"
                botManager = component "Bot Manager" "Manages bot lifecycle and operational state" "Python Classes"
            }

            webApp = container "Web Dashboard" "Real-time monitoring and control interface" "FastAPI, React" {
                webController = component "Web Controller" "Handles HTTP requests and responses" "FastAPI Routes"
                authService = component "Authentication Service" "Manages user authentication and authorization" "JWT, OAuth2"
                dashboardUI = component "Dashboard UI" "Real-time trading dashboard with charts and controls" "React, WebSocket"
                apiGateway = component "API Gateway" "Exposes REST endpoints for external integrations" "FastAPI"
            }

            tradingBot = container "Trading Bot Core" "Main trading engine with strategy execution" "Python, AsyncIO" {
                botController = component "Bot Controller" "Main orchestrator managing bot lifecycle and coordination" "PassivBot Class"
                configManager = component "Configuration Manager" "Loads, validates, and manages configuration data" "Pydantic Models"
                riskManager = component "Risk Manager" "Monitors drawdown, position sizes, and implements safety stops" "Risk Controller"
                
                exchangeManager = component "Exchange Manager" "Manages exchange connections and abstracts trading operations" "Exchange Registry"
                binanceImpl = component "Binance Implementation" "Binance-specific API integration and order handling" "BinanceExchange Class"
                bybitImpl = component "Bybit Implementation" "Bybit-specific API integration and order handling" "BybitExchange Class"
                
                strategyManager = component "Strategy Manager" "Orchestrates trading strategies and execution logic" "Strategy Registry"
                gridStrategy = component "Grid Strategy" "Grid trading algorithm with buy/sell level management" "GridStrategy Class"
                dcaStrategy = component "DCA Strategy" "Dollar cost averaging algorithm with safety orders" "DCAStrategy Class"
                
                orderManager = component "Order Manager" "Manages order lifecycle, placement, and tracking" "Order Controller"
                positionTracker = component "Position Tracker" "Tracks open positions, P&L, and portfolio state" "Position Monitor"
                marketDataHandler = component "Market Data Handler" "Processes real-time market data and price feeds" "Data Processor"
                notificationService = component "Notification Service" "Sends alerts and notifications to external services" "Alert Manager"
            }

            database = container "Database" "Persistent storage for trading data and configurations" "SQLite/PostgreSQL" {
                tradingData = component "Trading Data Store" "Stores order history, trades, and performance metrics" "SQL Tables"
                configData = component "Configuration Store" "Stores bot configurations and strategy parameters" "SQL Tables"
                auditLog = component "Audit Log" "Stores system events and trading activity for compliance" "SQL Tables"
            }

            configStore = container "Configuration Storage" "External configuration files and parameters" "JSON/YAML Files" {
                strategyConfigs = component "Strategy Configurations" "Trading strategy parameters and settings" "YAML Files"
                exchangeConfigs = component "Exchange Configurations" "API credentials and exchange-specific settings" "JSON Files"
                riskConfigs = component "Risk Parameters" "Risk management rules and safety limits" "YAML Files"
            }
        }

        # Relationships - User to System
        trader -> passivbotSystem "Configures strategies and monitors trading performance"
        trader -> cliApp "Manages bot via command-line interface"
        trader -> webApp "Monitors performance via web dashboard"

        # Relationships - System to External Systems
        passivbotSystem -> binanceExchange "Places orders and retrieves market data" "REST API/WebSocket"
        passivbotSystem -> bybitExchange "Places orders and retrieves market data" "REST API/WebSocket"
        passivbotSystem -> telegramService "Sends trading notifications and alerts" "Bot API"
        passivbotSystem -> discordService "Sends trading notifications and alerts" "Webhook API"

        # Relationships - Container Level
        cliApp -> tradingBot "Controls bot lifecycle and configuration" "Direct Method Calls"
        webApp -> tradingBot "Retrieves status and controls bot operations" "HTTP API"
        tradingBot -> database "Stores and retrieves trading data" "SQL Queries"
        tradingBot -> configStore "Reads configuration parameters" "File I/O"

        # Relationships - Component Level (CLI)
        cliController -> configValidator "Validates configuration files"
        cliController -> botManager "Manages bot operations"
        botManager -> botController "Controls bot lifecycle"

        # Relationships - Component Level (Web)
        dashboardUI -> webController "Sends user interactions"
        webController -> authService "Authenticates users"
        webController -> apiGateway "Proxies API requests"
        apiGateway -> botController "Retrieves bot status and controls"

        # Relationships - Component Level (Trading Bot)
        botController -> configManager "Loads configuration"
        botController -> riskManager "Performs risk checks"
        botController -> exchangeManager "Executes exchange operations"
        botController -> strategyManager "Executes trading strategies"
        botController -> notificationService "Sends notifications"

        exchangeManager -> binanceImpl "Delegates Binance operations"
        exchangeManager -> bybitImpl "Delegates Bybit operations"
        binanceImpl -> binanceExchange "Makes API calls"
        bybitImpl -> bybitExchange "Makes API calls"

        strategyManager -> gridStrategy "Executes grid trading logic"
        strategyManager -> dcaStrategy "Executes DCA trading logic"
        gridStrategy -> orderManager "Places and manages orders"
        dcaStrategy -> orderManager "Places and manages orders"

        orderManager -> exchangeManager "Submits orders to exchanges"
        positionTracker -> exchangeManager "Retrieves position updates"
        marketDataHandler -> exchangeManager "Receives market data"
        notificationService -> telegramService "Sends notifications"
        notificationService -> discordService "Sends notifications"

        # Relationships - Database
        botController -> tradingData "Stores trading events"
        orderManager -> tradingData "Stores order history"
        positionTracker -> tradingData "Stores position data"
        configManager -> configData "Retrieves configuration"
        botController -> auditLog "Logs system events"

        # Relationships - Configuration
        configManager -> strategyConfigs "Reads strategy parameters"
        configManager -> exchangeConfigs "Reads exchange settings"
        configManager -> riskConfigs "Reads risk parameters"
    }

    views {
        # System Context View
        systemContext passivbotSystem "SystemContext" {
            include *
            autoLayout
            description "System context diagram showing Passivbot's interactions with users and external systems"
        }

        # Container View
        container passivbotSystem "Containers" {
            include *
            autoLayout
            description "Container diagram showing the major containers that make up Passivbot"
        }

        # Component View - Trading Bot Core
        component tradingBot "TradingBotComponents" {
            include *
            autoLayout
            description "Component diagram showing the internal structure of the Trading Bot Core"
        }

        # Component View - CLI Application
        component cliApp "CLIComponents" {
            include *
            autoLayout
            description "Component diagram showing the internal structure of the CLI Application"
        }

        # Component View - Web Application
        component webApp "WebComponents" {
            include *
            autoLayout
            description "Component diagram showing the internal structure of the Web Dashboard"
        }

        # Deployment View
        deployment passivbotSystem "Live" "Deployment" {
            deploymentNode "User's Computer" "Windows/Mac/Linux" "User's local machine" {
                containerInstance cliApp
                containerInstance configStore
            }

            deploymentNode "Cloud Server" "Ubuntu 22.04" "VPS or cloud instance" {
                containerInstance tradingBot
                containerInstance webApp
                containerInstance database
                
                deploymentNode "Reverse Proxy" "Nginx" "Load balancer and SSL termination" {
                    infrastructureNode "SSL Certificate" "TLS encryption"
                }
            }

            deploymentNode "Exchange Infrastructure" "Cloud" "External exchange servers" {
                infrastructureNode "Binance API" "REST/WebSocket endpoints"
                infrastructureNode "Bybit API" "REST/WebSocket endpoints"
            }

            autoLayout
            description "Deployment diagram showing how Passivbot is deployed across different environments"
        }

        # Dynamic View - Trading Flow
        dynamic tradingBot "TradingFlow" "Trading Execution Flow" {
            marketDataHandler -> strategyManager "Market data update"
            strategyManager -> gridStrategy "Execute grid strategy"
            gridStrategy -> riskManager "Check risk limits"
            riskManager -> orderManager "Risk approved"
            orderManager -> exchangeManager "Place order"
            exchangeManager -> binanceImpl "Submit to Binance"
            binanceImpl -> orderManager "Order confirmation"
            orderManager -> positionTracker "Update positions"
            positionTracker -> notificationService "Position update"
            notificationService -> telegramService "Send notification"
            
            autoLayout
            description "Dynamic diagram showing the flow of a typical trading operation"
        }

        # Styles
        styles {
            element "Person" {
                shape Person
                background #1e88e5
                color #ffffff
            }
            element "Software System" {
                background #1565c0
                color #ffffff
            }
            element "External" {
                background #616161
                color #ffffff
            }
            element "Container" {
                background #42a5f5
                color #ffffff
            }
            element "Component" {
                background #90caf9
                color #000000
            }
            element "Infrastructure Node" {
                background #ffcc02
                color #000000
            }
        }

        # Themes
        theme default
    }

    configuration {
        scope softwaresystem
    }
}
