"""Command line interface for Passivbot."""

import asyncio
import json
import sys
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.live import Live
from rich.text import Text
import uvicorn

from .core.config import PassivbotConfig, create_default_config, validate_configuration
from .core.exceptions import PassivbotError, ConfigurationError
from . import PassivBot, BotManager, __version__

app = typer.Typer(
    name="passivbot",
    help="Advanced cryptocurrency trading bot with grid and DCA strategies",
    add_completion=False,
)
console = Console()


@app.command()
def version() -> None:
    """Show version information."""
    console.print(f"Passivbot v{__version__}")


@app.command()
def init(
    config_path: str = typer.Option("config.json", help="Configuration file path"),
    exchange: str = typer.Option("binance", help="Exchange type"),
    symbol: str = typer.Option("BTCUSDT", help="Trading symbol"),
    strategy: str = typer.Option("grid", help="Strategy type"),
) -> None:
    """Initialize a new configuration file."""
    config_file = Path(config_path)
    
    if config_file.exists():
        if not typer.confirm(f"Configuration file {config_path} already exists. Overwrite?"):
            raise typer.Abort()
    
    # Create default configuration
    config_data = create_default_config()
    
    # Update with user preferences
    config_data["exchange"]["type"] = exchange
    config_data["strategies"][0]["symbol"] = symbol
    config_data["strategies"][0]["type"] = strategy
    
    # Save configuration
    with open(config_file, 'w') as f:
        json.dump(config_data, f, indent=2)
    
    console.print(f"✅ Configuration file created: {config_path}")
    console.print("📝 Edit the configuration file to add your API keys and adjust settings.")


@app.command()
def validate(
    config_path: str = typer.Option("config.json", help="Configuration file path"),
) -> None:
    """Validate configuration file."""
    try:
        config = PassivbotConfig.from_file(config_path)
        warnings = validate_configuration(config)
        
        if warnings:
            console.print("⚠️  Configuration warnings:")
            for warning in warnings:
                console.print(f"  • {warning}")
        else:
            console.print("✅ Configuration is valid")
            
    except FileNotFoundError:
        console.print(f"❌ Configuration file not found: {config_path}")
        raise typer.Exit(1)
    except ConfigurationError as e:
        console.print(f"❌ Configuration error: {e}")
        raise typer.Exit(1)


@app.command()
def run(
    config_path: str = typer.Option("config.json", help="Configuration file path"),
    dry_run: bool = typer.Option(False, help="Run in dry mode (no real trades)"),
) -> None:
    """Run the trading bot."""
    try:
        # Load and validate configuration
        config = PassivbotConfig.from_file(config_path)
        
        # Override dry run if specified
        if dry_run:
            config.dry_run = True
        
        # Validate configuration
        warnings = validate_configuration(config)
        if warnings:
            console.print("⚠️  Configuration warnings:")
            for warning in warnings:
                console.print(f"  • {warning}")
            
            if not typer.confirm("Continue anyway?"):
                raise typer.Abort()
        
        # Show startup information
        _show_startup_info(config)
        
        # Run the bot
        asyncio.run(_run_bot_async(config))
        
    except FileNotFoundError:
        console.print(f"❌ Configuration file not found: {config_path}")
        console.print("💡 Use 'passivbot init' to create a configuration file.")
        raise typer.Exit(1)
    except ConfigurationError as e:
        console.print(f"❌ Configuration error: {e}")
        raise typer.Exit(1)
    except KeyboardInterrupt:
        console.print("\n🛑 Bot stopped by user")
    except PassivbotError as e:
        console.print(f"❌ Bot error: {e}")
        raise typer.Exit(1)


@app.command()
def status(
    config_path: str = typer.Option("config.json", help="Configuration file path"),
) -> None:
    """Show bot status and portfolio information."""
    try:
        config = PassivbotConfig.from_file(config_path)
        asyncio.run(_show_status_async(config))
        
    except FileNotFoundError:
        console.print(f"❌ Configuration file not found: {config_path}")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"❌ Error: {e}")
        raise typer.Exit(1)


@app.command()
def web(
    config_path: str = typer.Option("config.json", help="Configuration file path"),
    host: Optional[str] = typer.Option(None, help="Web server host"),
    port: Optional[int] = typer.Option(None, help="Web server port"),
) -> None:
    """Start the web interface."""
    try:
        config = PassivbotConfig.from_file(config_path)
        
        # Override host/port if specified
        web_host = host or config.web.host
        web_port = port or config.web.port
        
        console.print(f"🌐 Starting web interface at http://{web_host}:{web_port}")
        
        # Start web server
        uvicorn.run(
            "passivbot.web.app:app",
            host=web_host,
            port=web_port,
            log_level="info"
        )
        
    except FileNotFoundError:
        console.print(f"❌ Configuration file not found: {config_path}")
        raise typer.Exit(1)
    except ImportError:
        console.print("❌ Web interface dependencies not available")
        console.print("💡 Install with: pip install 'passivbot[web]'")
        raise typer.Exit(1)


def _show_startup_info(config: PassivbotConfig) -> None:
    """Show startup information."""
    # Create startup panel
    startup_text = f"""
🤖 Passivbot v{__version__}

📊 Exchange: {config.exchange.type.upper()}
🔄 Strategies: {len(config.strategies)}
🎯 Symbols: {', '.join(s.symbol for s in config.strategies)}
⚡ Dry Run: {'Yes' if config.dry_run else 'No'}
📈 Risk Management: Max Drawdown {config.risk.max_drawdown_percentage}%
    """.strip()
    
    console.print(Panel(startup_text, title="🚀 Starting Passivbot", border_style="green"))
    
    # Show strategies table
    table = Table(title="📋 Configured Strategies")
    table.add_column("Symbol", style="cyan")
    table.add_column("Type", style="magenta")
    table.add_column("Status", style="green")
    
    for strategy in config.strategies:
        status = "✅ Enabled" if strategy.enabled else "❌ Disabled"
        table.add_row(strategy.symbol, strategy.type, status)
    
    console.print(table)


async def _run_bot_async(config: PassivbotConfig) -> None:
    """Run bot asynchronously with live status display."""
    async with BotManager(config) as bot:
        # Create live display for bot status
        with Live(_create_status_table(bot), refresh_per_second=1) as live:
            # Start bot in background
            bot_task = asyncio.create_task(bot.start())
            
            try:
                # Update display while bot runs
                while not bot_task.done():
                    live.update(_create_status_table(bot))
                    await asyncio.sleep(1)
                
                # Check if bot task completed with exception
                await bot_task
                
            except KeyboardInterrupt:
                console.print("\n🛑 Stopping bot...")
                await bot.stop()


async def _show_status_async(config: PassivbotConfig) -> None:
    """Show current bot status."""
    # This would connect to running bot instance or show saved state
    console.print("📊 Bot Status: Not implemented yet")
    console.print("💡 This feature will show real-time bot status in future versions")


def _create_status_table(bot: PassivBot) -> Table:
    """Create status table for live display."""
    table = Table(title="🤖 Bot Status")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="white")
    
    status = bot.status
    table.add_row("Status", "🟢 Running" if status["running"] else "🔴 Stopped")
    table.add_row("Mode", "🧪 Dry Run" if status["dry_run"] else "💰 Live Trading")
    table.add_row("Exchange", status["exchange"].upper())
    table.add_row("Strategies", str(status["strategies"]))
    table.add_row("Active Positions", str(status["positions"]))
    table.add_row("Open Orders", str(status["orders"]))
    
    return table


def main() -> None:
    """Main CLI entry point."""
    try:
        app()
    except KeyboardInterrupt:
        console.print("\n👋 Goodbye!")
        sys.exit(0)
    except Exception as e:
        console.print(f"❌ Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
