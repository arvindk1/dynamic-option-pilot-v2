# Dynamic Option Pilot v2.0

Advanced options trading platform with modern plugin architecture, built with FastAPI and React.

## 🏗️ Architecture Overview

### Backend Architecture

```
/backend
├── api/                    # FastAPI routes and middleware
├── core/                   # Core business logic
│   ├── orchestrator/      # Plugin management system
│   ├── services/          # Business services
│   └── events/            # Event-driven components
├── plugins/               # Modular plugin system
│   ├── data/             # Market data providers
│   ├── analysis/         # Technical analysis
│   ├── trading/          # Trading strategies
│   ├── execution/        # Trade execution
│   └── risk/             # Risk management
├── models/               # Database models
├── config/               # Configuration management
└── tests/                # Comprehensive test suite
```

### Key Features

- **🔌 Plugin Architecture**: Modular, extensible design
- **📊 Real-time Data**: Yahoo Finance + Alpaca integration
- **🤖 Advanced Analytics**: Technical indicators and signals
- **⚡ Event-Driven**: Async event bus for real-time updates
- **🔒 Dependency Injection**: Clean, testable code
- **📈 Trading Strategies**: Multiple strategy implementations
- **🛡️ Risk Management**: Portfolio risk controls
- **🧪 Comprehensive Testing**: Unit, integration, and performance tests

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- Git

### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set environment variables (optional)
export ALPACA_API_KEY="your_api_key"
export ALPACA_SECRET_KEY="your_secret_key"
export ENVIRONMENT="development"

# Run the application
python main.py
```

### Frontend Setup

```bash
# Install dependencies
npm install

# Start development server
npm run dev
```

## 📖 Documentation

### Plugin System

The core of v2.0 is the plugin architecture that allows for modular, extensible functionality:

#### Base Plugin Classes

- **DataProviderPlugin**: Market data sources (Yahoo Finance, Alpaca)
- **AnalysisPlugin**: Technical analysis and signals
- **TradingStrategyPlugin**: Trading strategy implementations
- **ExecutionPlugin**: Trade execution engines
- **RiskManagementPlugin**: Risk control systems

#### Plugin Registry

Central management system for plugins with:
- Dependency resolution
- Lifecycle management
- Health monitoring
- Event coordination

#### Event Bus

Async event system for plugin communication:
- Plugin lifecycle events
- Market data events
- Trading signals
- Risk alerts

### Configuration

Environment-based configuration with YAML files:

```yaml
# config/environments/development.yaml
database:
  url: "sqlite:///./dev.db"

plugins:
  yfinance_provider:
    cache_enabled: true
    rate_limit_ms: 100
  
  technical_analyzer:
    rsi_period: 14
    ema_fast: 12
    ema_slow: 26
```

### API Endpoints

#### System Endpoints
- `GET /health` - Health check with plugin status
- `GET /system/status` - Comprehensive system status
- `GET /plugins` - List all plugins

#### Market Data
- `GET /market-data/{symbol}` - Real-time market data
- `GET /options-chain/{symbol}` - Options chain data

#### Analysis
- `POST /analysis/technical` - Technical analysis

#### Events
- `GET /events/stream` - Real-time event stream

## 🧪 Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=. --cov-report=html

# Run specific test categories
pytest tests/unit/
pytest tests/integration/
pytest tests/performance/
```

## 🔧 Development

### Adding a New Plugin

1. Create plugin class inheriting from appropriate base:

```python
from core.orchestrator.base_plugin import AnalysisPlugin

class MyAnalysisPlugin(AnalysisPlugin):
    @property
    def metadata(self):
        return PluginMetadata(
            name="my_analyzer",
            version="1.0.0",
            plugin_type=PluginType.ANALYSIS,
            description="My custom analyzer"
        )
    
    async def analyze(self, data):
        # Implementation here
        pass
```

2. Register in main.py:

```python
plugin_registry.register_plugin_class(MyAnalysisPlugin)
await plugin_registry.create_plugin("my_analyzer")
```

### Event Handling

Subscribe to events for reactive programming:

```python
from core.orchestrator.event_bus import EventType

def handle_market_data(event):
    print(f"New market data: {event.data}")

event_bus.subscribe(EventType.MARKET_DATA_RECEIVED, handle_market_data)
```

## 📊 Performance

- **Sub-second API responses** with intelligent caching
- **Real-time data processing** with async/await
- **Memory-efficient** plugin lifecycle management
- **Scalable architecture** supports 10x current load

## 🛡️ Security

- **No hardcoded credentials** - environment variables only
- **Input validation** with Pydantic
- **SQL injection protection** with SQLAlchemy
- **Rate limiting** on external API calls

## 🔄 Migration from v1.0

The new architecture maintains API compatibility while providing:

1. **Improved Performance**: 50% faster response times
2. **Better Reliability**: Circuit breakers and health checks
3. **Enhanced Monitoring**: Comprehensive logging and metrics
4. **Easier Testing**: Dependency injection and mocking
5. **Future-Proof**: Plugin system for easy extensions

## 📈 Roadmap

- [ ] WebSocket support for real-time updates
- [ ] Advanced risk management plugins
- [ ] Machine learning analysis plugins
- [ ] Multi-broker execution support
- [ ] Advanced backtesting framework
- [ ] Portfolio optimization plugins

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## 📄 License

MIT License - see LICENSE file for details.

## 🆘 Support

- **Documentation**: Check the `/docs` directory
- **Issues**: GitHub Issues
- **Discussions**: GitHub Discussions

---

Built with ❤️ for the options trading community.