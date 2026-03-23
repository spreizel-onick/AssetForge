"""Code-Generatoren: Wiederverwendbare Code-Snippets und Boilerplate."""

import json
from . import register, get_output_dir


# ── React Component ──────────────────────────────────────

@register(
    name="react-component",
    category="Code",
    description="Generiert eine React-Komponente (Function Component mit Props, Styles, Tests)",
    parameters=[
        {"name": "name", "type": "text", "description": "Komponenten-Name (z.B. UserCard)", "required": True},
        {"name": "variant", "type": "select", "options": ["functional", "arrow"],
         "description": "Funktions-Stil", "required": False},
        {"name": "typescript", "type": "boolean", "description": "TypeScript verwenden", "required": False},
        {"name": "styling", "type": "select", "options": ["css-modules", "tailwind", "styled-components", "none"],
         "description": "Styling-Methode", "required": False},
        {"name": "with_test", "type": "boolean", "description": "Test-Datei generieren", "required": False},
        {"name": "with_story", "type": "boolean", "description": "Storybook Story generieren", "required": False},
    ],
)
def generate_react_component(params: dict) -> dict:
    name = params.get("name", "MyComponent").strip()
    variant = params.get("variant", "functional")
    ts = params.get("typescript", False)
    styling = params.get("styling", "css-modules")
    with_test = params.get("with_test", False)
    with_story = params.get("with_story", False)

    ext = "tsx" if ts else "jsx"
    css_ext = "module.css"
    props_type = f"interface {name}Props {{\n  className?: string;\n  children?: React.ReactNode;\n}}" if ts else ""
    props_param = f"{{ className, children }}: {name}Props" if ts else "{ className, children }"

    files = []

    # Main component
    lines = []
    if ts:
        lines.append("import React from 'react';")
    else:
        lines.append("import React from 'react';")

    if styling == "css-modules":
        lines.append(f"import styles from './{name}.{css_ext}';")
    elif styling == "styled-components":
        lines.append("import styled from 'styled-components';")

    lines.append("")

    if ts and props_type:
        lines.append(props_type)
        lines.append("")

    if styling == "styled-components":
        lines.extend([
            f"const Wrapper = styled.div`",
            "  /* styles here */",
            "`;",
            "",
        ])

    if variant == "arrow":
        lines.append(f"const {name} = ({props_param}) => {{")
    else:
        lines.append(f"{'export default ' if styling != 'styled-components' else ''}function {name}({props_param}) {{")

    lines.append("  return (")

    if styling == "css-modules":
        lines.append(f'    <div className={{`${{styles.root}} ${{className || ""}}`}}>')
    elif styling == "tailwind":
        lines.append(f'    <div className={{`${{className || ""}}`}}>')
    elif styling == "styled-components":
        lines.append("    <Wrapper>")
    else:
        lines.append(f'    <div className={{className}}>')

    lines.append(f"      {{children}}")

    if styling == "styled-components":
        lines.append("    </Wrapper>")
    else:
        lines.append("    </div>")

    lines.append("  );")

    if variant == "arrow":
        lines.append("};")
        lines.append("")
        lines.append(f"export default {name};")
    else:
        lines.append("}")

    lines.append("")

    comp_dir = get_output_dir() / name
    comp_dir.mkdir(parents=True, exist_ok=True)

    comp_file = comp_dir / f"{name}.{ext}"
    comp_file.write_text("\n".join(lines), encoding="utf-8")
    files.append(str(comp_file))

    # CSS Module
    if styling == "css-modules":
        css_content = f".root {{\n  /* {name} styles */\n}}\n"
        css_file = comp_dir / f"{name}.{css_ext}"
        css_file.write_text(css_content, encoding="utf-8")
        files.append(str(css_file))

    # Index barrel
    index_file = comp_dir / f"index.{'ts' if ts else 'js'}"
    index_file.write_text(f"export {{ default }} from './{name}';\n", encoding="utf-8")
    files.append(str(index_file))

    # Test
    if with_test:
        test_lines = [
            f"import {{ render, screen }} from '@testing-library/react';",
            f"import {name} from './{name}';",
            "",
            f"describe('{name}', () => {{",
            f"  it('renders without crashing', () => {{",
            f"    render(<{name}>Test</{name}>);",
            f"    expect(screen.getByText('Test')).toBeInTheDocument();",
            "  });",
            "});",
            "",
        ]
        test_file = comp_dir / f"{name}.test.{ext}"
        test_file.write_text("\n".join(test_lines), encoding="utf-8")
        files.append(str(test_file))

    # Storybook
    if with_story:
        story_lines = [
            f"import type {{ Meta, StoryObj }} from '@storybook/react';" if ts else f"import {name} from './{name}';",
        ]
        if ts:
            story_lines.append(f"import {name} from './{name}';")
        story_lines.extend([
            "",
            ("const meta: Meta<typeof " + name + "> = {" if ts else "const meta = {"),
            f"  title: 'Components/{name}',",
            f"  component: {name},",
            "  tags: ['autodocs'],",
            "};",
            "",
            f"export default meta;",
            "",
            f"export const Default = {{",
            f"  args: {{",
            f"    children: '{name} Content',",
            "  },",
            "};",
            "",
        ])
        story_file = comp_dir / f"{name}.stories.{ext}"
        story_file.write_text("\n".join(story_lines), encoding="utf-8")
        files.append(str(story_file))

    features = [variant, styling]
    if ts:
        features.append("TypeScript")
    if with_test:
        features.append("Test")
    if with_story:
        features.append("Story")

    return {"files": files, "message": f"React Component '{name}' generiert ({', '.join(features)})"}


# ── Express Middleware ────────────────────────────────────

@register(
    name="express-middleware",
    category="Code",
    description="Generiert Express.js Middleware (Auth, Logging, CORS, Rate-Limit, Error-Handler)",
    parameters=[
        {"name": "type", "type": "select",
         "options": ["auth-jwt", "logger", "cors", "rate-limit", "error-handler", "validator"],
         "description": "Middleware-Typ", "required": True},
        {"name": "typescript", "type": "boolean", "description": "TypeScript verwenden", "required": False},
    ],
)
def generate_express_middleware(params: dict) -> dict:
    mw_type = params.get("type", "auth-jwt")
    ts = params.get("typescript", False)
    ext = "ts" if ts else "js"

    req_type = ": Request" if ts else ""
    res_type = ": Response" if ts else ""
    next_type = ": NextFunction" if ts else ""

    middlewares = {
        "auth-jwt": {
            "filename": f"auth.{ext}",
            "content": [
                "import jwt from 'jsonwebtoken';" if ts else "const jwt = require('jsonwebtoken');",
                "" if not ts else "import { Request, Response, NextFunction } from 'express';",
                "",
                f"const JWT_SECRET = process.env.JWT_SECRET || 'change-me';",
                "",
                f"{'export ' if ts else ''}function authenticate(req{req_type}, res{res_type}, next{next_type}) {{",
                "  const header = req.headers.authorization;",
                "  if (!header?.startsWith('Bearer ')) {",
                "    return res.status(401).json({ error: 'No token provided' });",
                "  }",
                "",
                "  try {",
                "    const token = header.split(' ')[1];",
                "    const decoded = jwt.verify(token, JWT_SECRET);",
                f"    {'(req as any)' if ts else 'req'}.user = decoded;",
                "    next();",
                "  } catch (err) {",
                "    return res.status(401).json({ error: 'Invalid token' });",
                "  }",
                "}",
                "",
                "module.exports = { authenticate };" if not ts else "",
            ],
        },
        "logger": {
            "filename": f"logger.{ext}",
            "content": [
                "" if not ts else "import { Request, Response, NextFunction } from 'express';",
                "",
                f"{'export ' if ts else ''}function requestLogger(req{req_type}, res{res_type}, next{next_type}) {{",
                "  const start = Date.now();",
                "",
                "  res.on('finish', () => {",
                "    const duration = Date.now() - start;",
                "    const log = `${req.method} ${req.originalUrl} ${res.statusCode} ${duration}ms`;",
                "    if (res.statusCode >= 400) {",
                "      console.error(`[ERROR] ${log}`);",
                "    } else {",
                "      console.log(`[${new Date().toISOString()}] ${log}`);",
                "    }",
                "  });",
                "",
                "  next();",
                "}",
                "",
                "module.exports = { requestLogger };" if not ts else "",
            ],
        },
        "cors": {
            "filename": f"cors.{ext}",
            "content": [
                "" if not ts else "import { Request, Response, NextFunction } from 'express';",
                "",
                "const ALLOWED_ORIGINS = (process.env.CORS_ORIGINS || 'http://localhost:3000').split(',');",
                "",
                f"{'export ' if ts else ''}function corsMiddleware(req{req_type}, res{res_type}, next{next_type}) {{",
                "  const origin = req.headers.origin;",
                "",
                "  if (origin && ALLOWED_ORIGINS.includes(origin)) {",
                "    res.setHeader('Access-Control-Allow-Origin', origin);",
                "    res.setHeader('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS');",
                "    res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization');",
                "    res.setHeader('Access-Control-Allow-Credentials', 'true');",
                "    res.setHeader('Access-Control-Max-Age', '86400');",
                "  }",
                "",
                "  if (req.method === 'OPTIONS') {",
                "    return res.status(204).send();",
                "  }",
                "",
                "  next();",
                "}",
                "",
                "module.exports = { corsMiddleware };" if not ts else "",
            ],
        },
        "rate-limit": {
            "filename": f"rate-limit.{ext}",
            "content": [
                "" if not ts else "import { Request, Response, NextFunction } from 'express';",
                "",
                ("const requests: Map<string, number[]> = new Map();" if ts else "const requests = new Map();"),
                "const WINDOW_MS = 60 * 1000; // 1 minute",
                "const MAX_REQUESTS = 100;",
                "",
                f"{'export ' if ts else ''}function rateLimit(req{req_type}, res{res_type}, next{next_type}) {{",
                "  const ip = req.ip || req.socket.remoteAddress || 'unknown';",
                "  const now = Date.now();",
                "",
                "  if (!requests.has(ip)) {",
                "    requests.set(ip, []);",
                "  }",
                "",
                "  const timestamps = requests.get(ip).filter(t => now - t < WINDOW_MS);",
                "  timestamps.push(now);",
                "  requests.set(ip, timestamps);",
                "",
                "  res.setHeader('X-RateLimit-Limit', MAX_REQUESTS);",
                "  res.setHeader('X-RateLimit-Remaining', Math.max(0, MAX_REQUESTS - timestamps.length));",
                "",
                "  if (timestamps.length > MAX_REQUESTS) {",
                "    return res.status(429).json({ error: 'Too many requests, try again later' });",
                "  }",
                "",
                "  next();",
                "}",
                "",
                "module.exports = { rateLimit };" if not ts else "",
            ],
        },
        "error-handler": {
            "filename": f"error-handler.{ext}",
            "content": [
                "" if not ts else "import { Request, Response, NextFunction } from 'express';",
                "",
                f"{'export ' if ts else ''}function errorHandler(err{': Error' if ts else ''}, req{req_type}, res{res_type}, next{next_type}) {{",
                "  console.error(`[Error] ${err.message}`);",
                "  if (err.stack) console.error(err.stack);",
                "",
                "  const status = err.status || err.statusCode || 500;",
                "  const message = process.env.NODE_ENV === 'production'",
                "    ? 'Internal Server Error'",
                "    : err.message;",
                "",
                "  res.status(status).json({",
                "    error: {",
                "      message,",
                "      status,",
                "      ...(process.env.NODE_ENV !== 'production' && { stack: err.stack }),",
                "    },",
                "  });",
                "}",
                "",
                f"{'export ' if ts else ''}function notFoundHandler(req{req_type}, res{res_type}) {{",
                "  res.status(404).json({ error: { message: 'Not Found', status: 404 } });",
                "}",
                "",
                "module.exports = { errorHandler, notFoundHandler };" if not ts else "",
            ],
        },
        "validator": {
            "filename": f"validator.{ext}",
            "content": [
                "" if not ts else "import { Request, Response, NextFunction } from 'express';",
                "",
                "/**",
                " * Simple request body validator middleware.",
                " * Usage: app.post('/users', validateBody(['name', 'email']), handler)",
                " */",
                f"{'export ' if ts else ''}function validateBody(requiredFields{': string[]' if ts else ''}) {{",
                f"  return (req{req_type}, res{res_type}, next{next_type}) => {{",
                "    const missing = requiredFields.filter(f => !(f in req.body));",
                "    if (missing.length > 0) {",
                "      return res.status(400).json({",
                "        error: `Missing required fields: ${missing.join(', ')}`,",
                "      });",
                "    }",
                "    next();",
                "  };",
                "}",
                "",
                f"{'export ' if ts else ''}function validateQuery(allowedFields{': string[]' if ts else ''}) {{",
                f"  return (req{req_type}, res{res_type}, next{next_type}) => {{",
                "    const unknown = Object.keys(req.query).filter(f => !allowedFields.includes(f));",
                "    if (unknown.length > 0) {",
                "      return res.status(400).json({",
                "        error: `Unknown query parameters: ${unknown.join(', ')}`,",
                "      });",
                "    }",
                "    next();",
                "  };",
                "}",
                "",
                "module.exports = { validateBody, validateQuery };" if not ts else "",
            ],
        },
    }

    mw = middlewares[mw_type]
    middleware_dir = get_output_dir() / "middleware"
    middleware_dir.mkdir(exist_ok=True)
    out = middleware_dir / mw["filename"]
    content = "\n".join(line for line in mw["content"] if line is not None)
    out.write_text(content + "\n", encoding="utf-8")

    return {"files": [str(out)], "message": f"Express Middleware '{mw_type}' generiert ({'TypeScript' if ts else 'JavaScript'})"}


# ── Python Decorator / Utility ───────────────────────────

@register(
    name="python-util",
    category="Code",
    description="Generiert Python-Utility Module (Decorator, Logger, Config, Retry, Singleton)",
    parameters=[
        {"name": "type", "type": "select",
         "options": ["decorators", "logger", "config-loader", "retry", "singleton", "timer"],
         "description": "Utility-Typ", "required": True},
        {"name": "with_tests", "type": "boolean", "description": "Tests generieren (pytest)", "required": False},
    ],
)
def generate_python_util(params: dict) -> dict:
    util_type = params.get("type", "decorators")
    with_tests = params.get("with_tests", False)

    files = []

    utils = {
        "decorators": {
            "filename": "decorators.py",
            "content": '''"""Common Python decorators — generated by AssetForge."""

import functools
import time
import logging

logger = logging.getLogger(__name__)


def timer(func):
    """Log execution time of a function."""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = func(*args, **kwargs)
        elapsed = time.perf_counter() - start
        logger.info(f"{func.__name__} took {elapsed:.4f}s")
        return result
    return wrapper


def retry(max_attempts=3, delay=1.0, exceptions=(Exception,)):
    """Retry a function on failure."""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_exc = None
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exc = e
                    logger.warning(f"{func.__name__} attempt {attempt}/{max_attempts} failed: {e}")
                    if attempt < max_attempts:
                        time.sleep(delay * attempt)
            raise last_exc
        return wrapper
    return decorator


def cache(maxsize=128):
    """Simple LRU cache decorator (alias for functools.lru_cache)."""
    return functools.lru_cache(maxsize=maxsize)


def deprecated(message=""):
    """Mark a function as deprecated."""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            import warnings
            warnings.warn(
                f"{func.__name__} is deprecated. {message}",
                DeprecationWarning,
                stacklevel=2,
            )
            return func(*args, **kwargs)
        return wrapper
    return decorator


def validate_types(**type_hints):
    """Runtime type checking decorator."""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            import inspect
            sig = inspect.signature(func)
            bound = sig.bind(*args, **kwargs)
            bound.apply_defaults()
            for param_name, expected_type in type_hints.items():
                if param_name in bound.arguments:
                    value = bound.arguments[param_name]
                    if not isinstance(value, expected_type):
                        raise TypeError(
                            f"{param_name} must be {expected_type.__name__}, got {type(value).__name__}"
                        )
            return func(*args, **kwargs)
        return wrapper
    return decorator
''',
            "test": '''"""Tests for decorators module."""

import pytest
from decorators import timer, retry, deprecated, validate_types


def test_timer(capsys):
    @timer
    def fast_fn():
        return 42

    assert fast_fn() == 42


def test_retry_success():
    call_count = 0

    @retry(max_attempts=3, delay=0)
    def flaky():
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            raise ValueError("not yet")
        return "ok"

    assert flaky() == "ok"
    assert call_count == 3


def test_retry_failure():
    @retry(max_attempts=2, delay=0, exceptions=(ValueError,))
    def always_fails():
        raise ValueError("fail")

    with pytest.raises(ValueError):
        always_fails()


def test_validate_types():
    @validate_types(name=str, age=int)
    def greet(name, age):
        return f"{name} is {age}"

    assert greet("Alice", 30) == "Alice is 30"

    with pytest.raises(TypeError):
        greet("Alice", "thirty")
''',
        },
        "logger": {
            "filename": "log_config.py",
            "content": '''"""Structured logging configuration — generated by AssetForge."""

import logging
import logging.handlers
import json
import sys
from datetime import datetime, timezone


class JSONFormatter(logging.Formatter):
    """Format log records as JSON."""

    def format(self, record):
        log_data = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info and record.exc_info[0]:
            log_data["exception"] = self.formatException(record.exc_info)
        if hasattr(record, "extra_data"):
            log_data["data"] = record.extra_data
        return json.dumps(log_data)


def setup_logging(
    level: str = "INFO",
    json_format: bool = False,
    log_file: str | None = None,
    max_bytes: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5,
):
    """Configure application logging."""
    root = logging.getLogger()
    root.setLevel(getattr(logging, level.upper(), logging.INFO))

    # Clear existing handlers
    root.handlers.clear()

    if json_format:
        formatter = JSONFormatter()
    else:
        formatter = logging.Formatter(
            "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

    # Console handler
    console = logging.StreamHandler(sys.stdout)
    console.setFormatter(formatter)
    root.addHandler(console)

    # File handler (optional)
    if log_file:
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=max_bytes,
            backupCount=backup_count,
        )
        file_handler.setFormatter(formatter)
        root.addHandler(file_handler)

    return root


# Usage:
# from log_config import setup_logging
# logger = setup_logging(level="DEBUG", json_format=True, log_file="app.log")
''',
            "test": None,
        },
        "config-loader": {
            "filename": "config.py",
            "content": '''"""Environment-based configuration loader — generated by AssetForge."""

import os
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class DatabaseConfig:
    host: str = "localhost"
    port: int = 5432
    name: str = "app"
    user: str = "postgres"
    password: str = ""

    @property
    def url(self) -> str:
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.name}"


@dataclass
class AppConfig:
    debug: bool = False
    host: str = "0.0.0.0"
    port: int = 8000
    secret_key: str = "change-me-in-production"
    allowed_origins: list[str] = field(default_factory=lambda: ["http://localhost:3000"])
    db: DatabaseConfig = field(default_factory=DatabaseConfig)

    @classmethod
    def from_env(cls) -> "AppConfig":
        """Load configuration from environment variables."""
        return cls(
            debug=os.getenv("DEBUG", "false").lower() in ("true", "1", "yes"),
            host=os.getenv("HOST", "0.0.0.0"),
            port=int(os.getenv("PORT", "8000")),
            secret_key=os.getenv("SECRET_KEY", "change-me-in-production"),
            allowed_origins=os.getenv("CORS_ORIGINS", "http://localhost:3000").split(","),
            db=DatabaseConfig(
                host=os.getenv("DB_HOST", "localhost"),
                port=int(os.getenv("DB_PORT", "5432")),
                name=os.getenv("DB_NAME", "app"),
                user=os.getenv("DB_USER", "postgres"),
                password=os.getenv("DB_PASSWORD", ""),
            ),
        )


# Singleton instance
config = AppConfig.from_env()

# Usage:
# from config import config
# print(config.db.url)
# print(config.debug)
''',
            "test": None,
        },
        "retry": {
            "filename": "retry.py",
            "content": '''"""Retry utility with exponential backoff — generated by AssetForge."""

import time
import logging
import random
from functools import wraps

logger = logging.getLogger(__name__)


def retry(
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    jitter: bool = True,
    exceptions: tuple = (Exception,),
    on_retry=None,
):
    """
    Retry decorator with exponential backoff.

    Args:
        max_attempts: Maximum number of attempts.
        delay: Initial delay between retries in seconds.
        backoff: Multiplier for delay after each retry.
        jitter: Add random jitter to prevent thundering herd.
        exceptions: Tuple of exception types to catch.
        on_retry: Optional callback(attempt, exception) called on each retry.
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            current_delay = delay
            last_exception = None

            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt == max_attempts:
                        logger.error(f"{func.__name__} failed after {max_attempts} attempts: {e}")
                        raise

                    if on_retry:
                        on_retry(attempt, e)

                    sleep_time = current_delay
                    if jitter:
                        sleep_time += random.uniform(0, current_delay * 0.5)

                    logger.warning(
                        f"{func.__name__} attempt {attempt}/{max_attempts} failed: {e}. "
                        f"Retrying in {sleep_time:.2f}s..."
                    )
                    time.sleep(sleep_time)
                    current_delay *= backoff

            raise last_exception

        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            import asyncio
            current_delay = delay
            last_exception = None

            for attempt in range(1, max_attempts + 1):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt == max_attempts:
                        raise

                    sleep_time = current_delay
                    if jitter:
                        sleep_time += random.uniform(0, current_delay * 0.5)

                    logger.warning(f"{func.__name__} attempt {attempt} failed: {e}")
                    await asyncio.sleep(sleep_time)
                    current_delay *= backoff

            raise last_exception

        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return wrapper
    return decorator


# Usage:
# @retry(max_attempts=5, delay=0.5, exceptions=(ConnectionError, TimeoutError))
# def fetch_data(url):
#     ...
''',
            "test": None,
        },
        "singleton": {
            "filename": "singleton.py",
            "content": '''"""Singleton pattern implementations — generated by AssetForge."""

from threading import Lock


class SingletonMeta(type):
    """Thread-safe Singleton metaclass.

    Usage:
        class Database(metaclass=SingletonMeta):
            def __init__(self, url):
                self.url = url

        db1 = Database("postgres://...")
        db2 = Database("postgres://...")
        assert db1 is db2
    """

    _instances = {}
    _lock = Lock()

    def __call__(cls, *args, **kwargs):
        with cls._lock:
            if cls not in cls._instances:
                instance = super().__call__(*args, **kwargs)
                cls._instances[cls] = instance
            return cls._instances[cls]


def singleton(cls):
    """Singleton decorator.

    Usage:
        @singleton
        class Config:
            def __init__(self):
                self.data = {}
    """
    instances = {}
    lock = Lock()

    def get_instance(*args, **kwargs):
        with lock:
            if cls not in instances:
                instances[cls] = cls(*args, **kwargs)
            return instances[cls]

    return get_instance
''',
            "test": None,
        },
        "timer": {
            "filename": "timer.py",
            "content": '''"""Performance timing utilities — generated by AssetForge."""

import time
import logging
import functools
from contextlib import contextmanager

logger = logging.getLogger(__name__)


@contextmanager
def timer(label: str = "Block"):
    """Context manager to time a block of code.

    Usage:
        with timer("data loading"):
            load_data()
    """
    start = time.perf_counter()
    yield
    elapsed = time.perf_counter() - start
    logger.info(f"{label} took {elapsed:.4f}s")


def timed(func):
    """Decorator to time function execution.

    Usage:
        @timed
        def process():
            ...
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = func(*args, **kwargs)
        elapsed = time.perf_counter() - start
        logger.info(f"{func.__name__}() took {elapsed:.4f}s")
        return result
    return wrapper


class Stopwatch:
    """Reusable stopwatch with lap support.

    Usage:
        sw = Stopwatch()
        sw.start()
        # ... work ...
        sw.lap("phase 1")
        # ... more work ...
        sw.lap("phase 2")
        sw.stop()
        print(sw.summary())
    """

    def __init__(self):
        self._start = None
        self._laps = []
        self._end = None

    def start(self):
        self._start = time.perf_counter()
        self._laps = []
        self._end = None
        return self

    def lap(self, label: str = ""):
        if self._start is None:
            raise RuntimeError("Stopwatch not started")
        now = time.perf_counter()
        prev = self._laps[-1][1] if self._laps else self._start
        self._laps.append((label or f"Lap {len(self._laps) + 1}", now, now - prev))
        return self

    def stop(self):
        self._end = time.perf_counter()
        return self

    @property
    def elapsed(self) -> float:
        end = self._end or time.perf_counter()
        return end - (self._start or end)

    def summary(self) -> str:
        lines = [f"Total: {self.elapsed:.4f}s"]
        for label, _, duration in self._laps:
            lines.append(f"  {label}: {duration:.4f}s")
        return "\\n".join(lines)
''',
            "test": None,
        },
    }

    util = utils[util_type]
    utils_dir = get_output_dir() / "utils"
    utils_dir.mkdir(exist_ok=True)

    out = utils_dir / util["filename"]
    out.write_text(util["content"], encoding="utf-8")
    files.append(str(out))

    if with_tests and util.get("test"):
        test_dir = get_output_dir() / "tests"
        test_dir.mkdir(exist_ok=True)
        test_file = test_dir / f"test_{util['filename']}"
        test_file.write_text(util["test"], encoding="utf-8")
        files.append(str(test_file))

    return {"files": files, "message": f"Python Utility '{util_type}' generiert" + (" mit Tests" if with_tests and util.get("test") else "")}


# ── GitHub Actions Workflow ──────────────────────────────

@register(
    name="gh-action",
    category="Code",
    description="Generiert benutzerdefinierte GitHub Actions (Composite Action oder Reusable Workflow)",
    parameters=[
        {"name": "type", "type": "select", "options": ["composite-action", "reusable-workflow"],
         "description": "Action-Typ", "required": True},
        {"name": "name", "type": "text", "description": "Name der Action (z.B. deploy, lint-and-test)", "required": True},
        {"name": "purpose", "type": "select",
         "options": ["deploy", "lint-test", "docker-build", "release", "notify"],
         "description": "Zweck", "required": True},
    ],
)
def generate_gh_action(params: dict) -> dict:
    action_type = params.get("type", "composite-action")
    name = params.get("name", "my-action").strip().lower().replace(" ", "-")
    purpose = params.get("purpose", "deploy")

    files = []

    if action_type == "composite-action":
        purposes = {
            "deploy": {
                "description": f"Deploy application to production",
                "inputs": [
                    ("environment", "Deployment environment", True, "production"),
                    ("version", "Version to deploy", True, ""),
                ],
                "steps": [
                    {"name": "Checkout", "uses": "actions/checkout@v4"},
                    {"name": "Setup", "run": 'echo "Deploying version ${{ inputs.version }} to ${{ inputs.environment }}"'},
                    {"name": "Deploy", "run": "# Add deployment commands here\\necho 'Deployment complete'"},
                ],
            },
            "lint-test": {
                "description": "Run linting and tests",
                "inputs": [
                    ("node-version", "Node.js version", False, "20"),
                ],
                "steps": [
                    {"name": "Checkout", "uses": "actions/checkout@v4"},
                    {"name": "Setup Node.js", "uses": "actions/setup-node@v4", "with": {"node-version": "${{ inputs.node-version }}"}},
                    {"name": "Install dependencies", "run": "npm ci"},
                    {"name": "Lint", "run": "npm run lint"},
                    {"name": "Test", "run": "npm test"},
                ],
            },
            "docker-build": {
                "description": "Build and push Docker image",
                "inputs": [
                    ("image-name", "Docker image name", True, ""),
                    ("registry", "Container registry", False, "ghcr.io"),
                ],
                "steps": [
                    {"name": "Checkout", "uses": "actions/checkout@v4"},
                    {"name": "Set up Docker Buildx", "uses": "docker/setup-buildx-action@v3"},
                    {"name": "Log in to registry", "uses": "docker/login-action@v3", "with": {"registry": "${{ inputs.registry }}", "username": "${{ github.actor }}", "password": "${{ github.token }}"}},
                    {"name": "Build and push", "uses": "docker/build-push-action@v5", "with": {"push": "true", "tags": "${{ inputs.registry }}/${{ inputs.image-name }}:${{ github.sha }}"}},
                ],
            },
            "release": {
                "description": "Create a release with changelog",
                "inputs": [
                    ("version", "Release version (e.g., v1.0.0)", True, ""),
                    ("draft", "Create as draft", False, "false"),
                ],
                "steps": [
                    {"name": "Checkout", "uses": "actions/checkout@v4", "with": {"fetch-depth": "0"}},
                    {"name": "Generate changelog", "run": 'git log $(git describe --tags --abbrev=0 2>/dev/null || echo "")..HEAD --pretty=format:"- %s (%h)" > CHANGELOG_RELEASE.md'},
                    {"name": "Create Release", "uses": "softprops/action-gh-release@v1", "with": {"tag_name": "${{ inputs.version }}", "body_path": "CHANGELOG_RELEASE.md", "draft": "${{ inputs.draft }}"}},
                ],
            },
            "notify": {
                "description": "Send notifications (Slack/Discord)",
                "inputs": [
                    ("webhook-url", "Webhook URL", True, ""),
                    ("message", "Notification message", True, ""),
                    ("status", "Build status", False, "success"),
                ],
                "steps": [
                    {"name": "Send notification", "run": 'curl -X POST "${{ inputs.webhook-url }}" -H "Content-Type: application/json" -d \'{"text": "${{ inputs.message }} (Status: ${{ inputs.status }})"}\''},
                ],
            },
        }

        p = purposes[purpose]
        lines = [
            f"name: '{name}'",
            f"description: '{p['description']}'",
            "",
            "inputs:",
        ]
        for inp_name, inp_desc, inp_req, inp_default in p["inputs"]:
            lines.append(f"  {inp_name}:")
            lines.append(f"    description: '{inp_desc}'")
            lines.append(f"    required: {str(inp_req).lower()}")
            if inp_default:
                lines.append(f"    default: '{inp_default}'")

        lines.extend(["", "runs:", "  using: 'composite'", "  steps:"])

        for step in p["steps"]:
            lines.append(f"    - name: {step['name']}")
            if "uses" in step:
                lines.append(f"      uses: {step['uses']}")
                if "with" in step:
                    lines.append("      with:")
                    for k, v in step["with"].items():
                        lines.append(f"        {k}: {v}")
            if "run" in step:
                if "\\n" in step["run"]:
                    lines.append("      run: |")
                    for run_line in step["run"].split("\\n"):
                        lines.append(f"        {run_line}")
                else:
                    lines.append(f"      run: {step['run']}")
                lines.append("      shell: bash")

        action_dir = get_output_dir() / ".github" / "actions" / name
        action_dir.mkdir(parents=True, exist_ok=True)
        out = action_dir / "action.yml"
        out.write_text("\n".join(lines) + "\n", encoding="utf-8")
        files.append(str(out))

    else:  # reusable-workflow
        purposes_wf = {
            "deploy": f"""name: Deploy Workflow
on:
  workflow_call:
    inputs:
      environment:
        type: string
        required: true
        default: 'staging'
    secrets:
      DEPLOY_KEY:
        required: true

jobs:
  deploy:
    runs-on: ubuntu-latest
    environment: ${{{{ inputs.environment }}}}
    steps:
      - uses: actions/checkout@v4
      - name: Deploy
        run: echo "Deploying to ${{{{ inputs.environment }}}}"
        env:
          DEPLOY_KEY: ${{{{ secrets.DEPLOY_KEY }}}}
""",
            "lint-test": f"""name: Lint & Test Workflow
on:
  workflow_call:
    inputs:
      node-version:
        type: string
        default: '20'

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: ${{{{ inputs.node-version }}}}
          cache: 'npm'
      - run: npm ci
      - run: npm run lint

  test:
    runs-on: ubuntu-latest
    needs: lint
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: ${{{{ inputs.node-version }}}}
          cache: 'npm'
      - run: npm ci
      - run: npm test -- --coverage
      - uses: actions/upload-artifact@v4
        with:
          name: coverage
          path: coverage/
""",
            "docker-build": f"""name: Docker Build Workflow
on:
  workflow_call:
    inputs:
      image-name:
        type: string
        required: true
      push:
        type: boolean
        default: true

jobs:
  build:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      packages: write
    steps:
      - uses: actions/checkout@v4
      - uses: docker/setup-buildx-action@v3
      - uses: docker/login-action@v3
        with:
          registry: ghcr.io
          username: ${{{{ github.actor }}}}
          password: ${{{{ secrets.GITHUB_TOKEN }}}}
      - uses: docker/build-push-action@v5
        with:
          push: ${{{{ inputs.push }}}}
          tags: ghcr.io/${{{{ inputs.image-name }}}}:${{{{ github.sha }}}}
          cache-from: type=gha
          cache-to: type=gha,mode=max
""",
            "release": f"""name: Release Workflow
on:
  workflow_call:
    inputs:
      version:
        type: string
        required: true

jobs:
  release:
    runs-on: ubuntu-latest
    permissions:
      contents: write
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      - name: Generate changelog
        run: |
          git log $(git describe --tags --abbrev=0 2>/dev/null || echo "")..HEAD \\
            --pretty=format:"- %s (%h)" > RELEASE_NOTES.md
      - uses: softprops/action-gh-release@v1
        with:
          tag_name: ${{{{ inputs.version }}}}
          body_path: RELEASE_NOTES.md
          generate_release_notes: true
""",
            "notify": f"""name: Notification Workflow
on:
  workflow_call:
    inputs:
      status:
        type: string
        default: 'success'
      message:
        type: string
        default: 'Build completed'
    secrets:
      WEBHOOK_URL:
        required: true

jobs:
  notify:
    runs-on: ubuntu-latest
    steps:
      - name: Send Slack notification
        run: |
          curl -X POST "${{{{ secrets.WEBHOOK_URL }}}}" \\
            -H "Content-Type: application/json" \\
            -d '{{"text": "${{{{ inputs.message }}}} — Status: ${{{{ inputs.status }}}}"}}'
""",
        }

        wf_dir = get_output_dir() / ".github" / "workflows"
        wf_dir.mkdir(parents=True, exist_ok=True)
        out = wf_dir / f"{name}.yml"
        out.write_text(purposes_wf[purpose], encoding="utf-8")
        files.append(str(out))

    return {"files": files, "message": f"GitHub Action '{name}' generiert ({action_type}, {purpose})"}
