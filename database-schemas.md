# Database Schemas

This document provides a high-level overview of all database tables and their relationships in this repository.

---

## 1. Database Configuration & Base

**File:** `backend/models/database.py`

Defines the shared SQLAlchemy engine, session factory, and base metadata for all models.
```python
# backend/models/database.py
engine = create_engine(...)         # SQLite vs. Postgres/MySQL configuration
SessionLocal = sessionmaker(...)   # Session factory
Base = declarative_base()          # Declarative base for all models
get_db(), create_tables(), drop_tables()
```

## 2. Error‑Logging Models

### CriticalErrorLog (`critical_error_logs`)

**File:** `backend/models/error_log.py`
```python
class CriticalErrorLog(Base):
    __tablename__ = "critical_error_logs"
    id          = Column(String, primary_key=True, default=...)
    error_type  = Column(String, nullable=False, index=True)
    message     = Column(Text, nullable=False)
    details     = Column(JSON, nullable=True)
    created_at  = Column(DateTime, default=datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)
    severity    = Column(String, default="HIGH")
```

### SystemHealthStatus (`system_health_status`)

**File:** `backend/models/error_log.py`
```python
class SystemHealthStatus(Base):
    __tablename__ = "system_health_status"
    id              = Column(String, primary_key=True, default=...)
    check_timestamp = Column(DateTime, default=datetime.utcnow)
    service_name    = Column(String, nullable=False, index=True)
    status          = Column(String, nullable=False)
    response_time_ms= Column(String, nullable=True)
    error_count_24h = Column(String, nullable=True)
```

## 3. Opportunity / Scan‑Session Models

### ScanSession (`scan_sessions`)

**File:** `backend/models/opportunity.py`
```python
class ScanSession(Base):
    __tablename__ = "scan_sessions"
    id                  = Column(String, primary_key=True, default=...)
    strategy            = Column(String, index=True, nullable=False)
    started_at          = Column(DateTime, default=datetime.utcnow)
    completed_at        = Column(DateTime)
    opportunities_found = Column(Integer, default=0)
    status              = Column(String, default="RUNNING", index=True)
    opportunities       = relationship("OpportunitySnapshot", back_populates="scan_session")
```

### OpportunitySnapshot (`opportunity_snapshots`)

**File:** `backend/models/opportunity.py`
```python
class OpportunitySnapshot(Base):
    __tablename__ = "opportunity_snapshots"
    id              = Column(Integer, primary_key=True, index=True)
    opportunity_id  = Column(String, unique=True, index=True, nullable=False)
    symbol          = Column(String, index=True, nullable=False)
    strategy_type   = Column(String, index=True, nullable=False)
    data            = Column(JSON, nullable=False)
    created_at      = Column(DateTime, default=datetime.utcnow)
    expires_at      = Column(DateTime, nullable=False)
    scan_session_id = Column(String, ForeignKey("scan_sessions.id"), index=True)
```

## 4. Sandbox‑Only Models

Isolation layer for user testing and development of strategies.

### SandboxStrategyConfig (`sandbox_strategy_configs`)

**File:** `backend/models/sandbox.py`
```python
class SandboxStrategyConfig(Base):
    __tablename__ = "sandbox_strategy_configs"
    id          = Column(String, primary_key=True, default=...)
    strategy_id = Column(String, nullable=False)
    config_data = Column(JSON, nullable=False)
    is_active   = Column(Boolean, default=False)
    test_runs       = relationship("SandboxTestRun", back_populates="config")
    ai_conversations= relationship("SandboxAIConversation", back_populates="config")
```

### SandboxTestRun (`sandbox_test_runs`)

**File:** `backend/models/sandbox.py`
```python
class SandboxTestRun(Base):
    __tablename__ = "sandbox_test_runs"
    id                = Column(String, primary_key=True, default=...)
    config_id         = Column(String, ForeignKey("sandbox_strategy_configs.id"))
    test_parameters   = Column(JSON, nullable=False)
    opportunities_found=Column(Integer, default=0)
    test_results      = Column(JSON, nullable=False)
```

### SandboxAIConversation (`sandbox_ai_conversations`)

**File:** `backend/models/sandbox.py`
```python
class SandboxAIConversation(Base):
    __tablename__ = "sandbox_ai_conversations"
    id           = Column(String, primary_key=True, default=...)
    config_id    = Column(String, ForeignKey("sandbox_strategy_configs.id"))
    user_message = Column(Text, nullable=False)
    ai_response  = Column(Text, nullable=False)
```

### SandboxHistoricalCache (`sandbox_historical_cache`)

**File:** `backend/models/sandbox.py`
```python
class SandboxHistoricalCache(Base):
    __tablename__ = "sandbox_historical_cache"
    cache_key = Column(String, unique=True, nullable=False)
    symbol    = Column(String, nullable=False)
    data_type = Column(String, nullable=False)
    data      = Column(JSON, nullable=False)
    expires_at= Column(DateTime, nullable=False)
```

### SandboxStats (`sandbox_stats`)

**File:** `backend/models/sandbox.py`
```python
class SandboxStats(Base):
    __tablename__ = "sandbox_stats"
    id       = Column(String, primary_key=True, default=...)
    user_id  = Column(String, nullable=False)
    date     = Column(DateTime, default=func.now())
    strategies_created = Column(Integer, default=0)
```

## 5. Migration Script for Error‑Logging Tables

Raw SQL migration to create error‑logging tables if not using the ORM helper.

**File:** `backend/migrations/add_error_logging_tables.py`
```bash
# backend/migrations/add_error_logging_tables.py
python add_error_logging_tables.py
```
