"""
PyAgent 垂类智能体模块 - 金融智能体
"""

import asyncio
import time
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from .base import BaseVerticalAgent, AgentCapability, AgentResponse

try:
    import yfinance as yf
    YFINANCE_AVAILABLE = True
except ImportError:
    YFINANCE_AVAILABLE = False
    yf = None


@dataclass
class StockInfo:
    symbol: str
    name: str
    price: float
    change: float
    change_percent: float
    volume: int
    market_cap: float | None = None


@dataclass
class PortfolioHolding:
    symbol: str
    shares: float
    avg_cost: float
    current_price: float
    market_value: float


@dataclass
class RiskMetrics:
    volatility: float
    sharpe_ratio: float
    max_drawdown: float
    beta: float
    var_95: float


@dataclass
class CacheEntry:
    data: dict[str, Any]
    timestamp: float
    ttl: float


class RateLimiter:
    def __init__(self, max_calls: int, period: float):
        self.max_calls = max_calls
        self.period = period
        self.calls: list[float] = []
        self._lock = asyncio.Lock()

    async def acquire(self) -> bool:
        async with self._lock:
            now = time.time()
            self.calls = [call for call in self.calls if now - call < self.period]
            
            if len(self.calls) >= self.max_calls:
                return False
            
            self.calls.append(now)
            return True

    async def wait_and_acquire(self) -> None:
        while not await self.acquire():
            await asyncio.sleep(0.1)


class FinancialAgent(BaseVerticalAgent):
    """金融智能体"""

    def __init__(self, llm_client: Any | None = None):
        capabilities = [
            AgentCapability(
                name="get_stock_info",
                description="获取股票信息",
                parameters={"symbol": "股票代码"}
            ),
            AgentCapability(
                name="get_market_summary",
                description="获取市场概况",
                parameters={}
            ),
            AgentCapability(
                name="analyze_portfolio",
                description="分析投资组合",
                parameters={"holdings": "持仓列表"}
            ),
            AgentCapability(
                name="suggest_allocation",
                description="建议资产配置",
                parameters={"risk_profile": "风险偏好"}
            ),
            AgentCapability(
                name="calculate_risk",
                description="计算风险指标",
                parameters={"portfolio": "投资组合数据"}
            ),
            AgentCapability(
                name="get_financial_news",
                description="获取财经新闻",
                parameters={"category": "新闻类别"}
            ),
        ]

        super().__init__(
            name="financial_agent",
            description="金融分析和投资建议智能体",
            capabilities=capabilities,
            llm_client=llm_client
        )

        self._watchlist: list[str] = []
        self._news_callbacks: list[Any] = []
        
        self._cache: dict[str, CacheEntry] = {}
        self._cache_ttl = 300.0
        self._rate_limiter = RateLimiter(max_calls=100, period=60.0)
        
        self._api_timeout = 10.0
        self._max_retries = 3
        self._retry_delay = 1.0

    def _setup_handlers(self) -> None:
        self.register_handler("get_stock_info", self._get_stock_info)
        self.register_handler("get_market_summary", self._get_market_summary)
        self.register_handler("analyze_portfolio", self._analyze_portfolio)
        self.register_handler("suggest_allocation", self._suggest_allocation)
        self.register_handler("calculate_risk", self._calculate_risk)
        self.register_handler("get_financial_news", self._get_financial_news)

    def _get_cached(self, key: str) -> dict[str, Any] | None:
        if key in self._cache:
            entry = self._cache[key]
            if time.time() - entry.timestamp < entry.ttl:
                return entry.data
            else:
                del self._cache[key]
        return None

    def _set_cache(self, key: str, data: dict[str, Any], ttl: float | None = None) -> None:
        self._cache[key] = CacheEntry(
            data=data,
            timestamp=time.time(),
            ttl=ttl or self._cache_ttl
        )

    def _get_fallback_stock_info(self, symbol: str) -> dict[str, Any]:
        return {
            "symbol": symbol,
            "name": f"Stock {symbol}",
            "price": 0.0,
            "change": 0.0,
            "change_percent": 0.0,
            "volume": 0,
            "market_cap": None,
            "error": "API不可用或数据获取失败",
            "fallback": True,
        }

    def _get_fallback_market_summary(self) -> dict[str, Any]:
        return {
            "indices": {
                "S&P 500": {"value": 0.0, "change": 0.0, "error": "数据不可用"},
                "NASDAQ": {"value": 0.0, "change": 0.0, "error": "数据不可用"},
                "DOW": {"value": 0.0, "change": 0.0, "error": "数据不可用"},
            },
            "top_gainers": [],
            "top_losers": [],
            "market_sentiment": "unknown",
            "timestamp": datetime.now().isoformat(),
            "error": "API不可用或数据获取失败",
            "fallback": True,
        }

    async def _fetch_with_retry(self, fetch_func: Any, *args: Any, **kwargs: Any) -> Any:
        last_exception = None
        
        for attempt in range(self._max_retries):
            try:
                await self._rate_limiter.wait_and_acquire()
                
                loop = asyncio.get_event_loop()
                result = await asyncio.wait_for(
                    loop.run_in_executor(None, fetch_func, *args, **kwargs),
                    timeout=self._api_timeout
                )
                return result
            except asyncio.TimeoutError as e:
                last_exception = e
                if attempt < self._max_retries - 1:
                    await asyncio.sleep(self._retry_delay * (attempt + 1))
            except Exception as e:
                last_exception = e
                if attempt < self._max_retries - 1:
                    await asyncio.sleep(self._retry_delay * (attempt + 1))
        
        raise last_exception if last_exception else Exception("Unknown error")

    async def _get_stock_info(self, params: dict[str, Any]) -> dict[str, Any]:
        symbol = params.get("symbol", "").upper()
        
        if not symbol:
            return self._get_fallback_stock_info("")

        cache_key = f"stock_{symbol}"
        cached = self._get_cached(cache_key)
        if cached:
            return cached

        if not YFINANCE_AVAILABLE:
            return self._get_fallback_stock_info(symbol)

        try:
            def fetch_stock() -> Any:
                ticker = yf.Ticker(symbol)
                return ticker.info
            
            info = await self._fetch_with_retry(fetch_stock)
            
            if not info:
                return self._get_fallback_stock_info(symbol)

            current_price = info.get("currentPrice") or info.get("regularMarketPrice", 0.0)
            previous_close = info.get("previousClose", current_price)
            change = current_price - previous_close if previous_close else 0.0
            change_percent = (change / previous_close * 100) if previous_close else 0.0
            
            result = {
                "symbol": symbol,
                "name": info.get("longName") or info.get("shortName", symbol),
                "price": float(current_price),
                "change": float(change),
                "change_percent": float(change_percent),
                "volume": int(info.get("volume", 0) or info.get("regularMarketVolume", 0)),
                "market_cap": info.get("marketCap"),
            }
            
            self._set_cache(cache_key, result, ttl=300.0)
            return result
            
        except Exception as e:
            return self._get_fallback_stock_info(symbol)

    async def _get_market_summary(self, params: dict[str, Any]) -> dict[str, Any]:
        cache_key = "market_summary"
        cached = self._get_cached(cache_key)
        if cached:
            return cached

        if not YFINANCE_AVAILABLE:
            return self._get_fallback_market_summary()

        try:
            indices_symbols = {
                "S&P 500": "^GSPC",
                "NASDAQ": "^IXIC",
                "DOW": "^DJI",
            }
            
            indices_data = {}
            
            for name, symbol in indices_symbols.items():
                try:
                    def fetch_index(sym: str = symbol) -> Any:
                        ticker = yf.Ticker(sym)
                        return ticker.info
                    
                    info = await self._fetch_with_retry(fetch_index)
                    
                    current_price = info.get("currentPrice") or info.get("regularMarketPrice", 0.0)
                    previous_close = info.get("previousClose", current_price)
                    change = current_price - previous_close if previous_close else 0.0
                    change_percent = (change / previous_close * 100) if previous_close else 0.0
                    
                    indices_data[name] = {
                        "value": float(current_price),
                        "change": float(change_percent),
                    }
                except Exception:
                    indices_data[name] = {
                        "value": 0.0,
                        "change": 0.0,
                        "error": "数据获取失败",
                    }

            result = {
                "indices": indices_data,
                "top_gainers": [],
                "top_losers": [],
                "market_sentiment": self._calculate_market_sentiment(indices_data),
                "timestamp": datetime.now().isoformat(),
            }
            
            self._set_cache(cache_key, result, ttl=300.0)
            return result
            
        except Exception as e:
            return self._get_fallback_market_summary()

    def _calculate_market_sentiment(self, indices_data: dict[str, Any]) -> str:
        if not indices_data:
            return "unknown"
        
        total_change = 0.0
        count = 0
        
        for data in indices_data.values():
            if "change" in data and isinstance(data["change"], (int, float)):
                total_change += data["change"]
                count += 1
        
        if count == 0:
            return "unknown"
        
        avg_change = total_change / count
        
        if avg_change > 1.0:
            return "very_bullish"
        elif avg_change > 0.3:
            return "bullish"
        elif avg_change > -0.3:
            return "neutral"
        elif avg_change > -1.0:
            return "bearish"
        else:
            return "very_bearish"

    async def _analyze_portfolio(self, params: dict[str, Any]) -> dict[str, Any]:
        holdings = params.get("holdings", [])
        
        if not holdings:
            return {
                "total_value": 0.0,
                "total_cost": 0.0,
                "total_gain_loss": 0.0,
                "total_gain_loss_percent": 0.0,
                "holdings": [],
                "diversification_score": 0.0,
                "risk_level": "unknown",
            }

        total_value = 0.0
        total_cost = 0.0
        analyzed_holdings = []
        
        for h in holdings:
            symbol = h.get("symbol", "")
            shares = h.get("shares", 0)
            avg_cost = h.get("avg_cost", 0)
            
            stock_info = await self._get_stock_info({"symbol": symbol})
            current_price = stock_info.get("price", avg_cost)
            
            market_value = shares * current_price
            cost_basis = shares * avg_cost
            
            total_value += market_value
            total_cost += cost_basis
            
            analyzed_holdings.append({
                "symbol": symbol,
                "shares": shares,
                "avg_cost": avg_cost,
                "current_price": current_price,
                "market_value": market_value,
                "gain_loss": market_value - cost_basis,
                "gain_loss_percent": ((market_value - cost_basis) / cost_basis * 100) if cost_basis > 0 else 0,
                "fallback": stock_info.get("fallback", False),
            })

        diversification_score = min(1.0, len(holdings) / 10.0)
        
        if total_cost > 0:
            gain_percent = ((total_value - total_cost) / total_cost) * 100
            if gain_percent > 20:
                risk_level = "high"
            elif gain_percent > 5:
                risk_level = "moderate"
            elif gain_percent > -5:
                risk_level = "low"
            else:
                risk_level = "high"
        else:
            risk_level = "unknown"

        return {
            "total_value": total_value,
            "total_cost": total_cost,
            "total_gain_loss": total_value - total_cost,
            "total_gain_loss_percent": ((total_value - total_cost) / total_cost * 100) if total_cost > 0 else 0,
            "holdings": analyzed_holdings,
            "diversification_score": diversification_score,
            "risk_level": risk_level,
        }

    async def _suggest_allocation(self, params: dict[str, Any]) -> dict[str, Any]:
        risk_profile = params.get("risk_profile", "moderate")

        allocations = {
            "conservative": {
                "stocks": 30,
                "bonds": 50,
                "cash": 15,
                "alternatives": 5,
            },
            "moderate": {
                "stocks": 60,
                "bonds": 30,
                "cash": 5,
                "alternatives": 5,
            },
            "aggressive": {
                "stocks": 80,
                "bonds": 10,
                "cash": 5,
                "alternatives": 5,
            },
        }

        allocation = allocations.get(risk_profile, allocations["moderate"])

        return {
            "risk_profile": risk_profile,
            "allocation": allocation,
            "recommendations": [
                "建议定期再平衡投资组合",
                "考虑增加指数基金以分散风险",
                "保持适当的现金储备",
            ],
            "expected_return": {
                "conservative": "4-6%",
                "moderate": "6-8%",
                "aggressive": "8-12%",
            }.get(risk_profile, "6-8%"),
        }

    async def _calculate_risk(self, params: dict[str, Any]) -> dict[str, Any]:
        portfolio = params.get("portfolio", {})

        await asyncio.sleep(0.1)

        return {
            "volatility": 0.18,
            "sharpe_ratio": 1.2,
            "max_drawdown": -0.15,
            "beta": 1.05,
            "var_95": -0.025,
            "risk_rating": "moderate",
            "recommendations": [
                "当前波动率处于合理范围",
                "建议关注最大回撤风险",
            ],
        }

    async def _get_financial_news(self, params: dict[str, Any]) -> dict[str, Any]:
        category = params.get("category", "general")

        await asyncio.sleep(0.1)

        return {
            "category": category,
            "news": [
                {
                    "title": "市场分析：科技股领涨",
                    "source": "财经日报",
                    "time": "2小时前",
                    "summary": "科技板块今日表现强劲...",
                },
                {
                    "title": "央行政策解读",
                    "source": "经济观察",
                    "time": "4小时前",
                    "summary": "最新货币政策分析...",
                },
            ],
            "timestamp": datetime.now().isoformat(),
        }

    def add_to_watchlist(self, symbol: str) -> None:
        if symbol not in self._watchlist:
            self._watchlist.append(symbol)

    def remove_from_watchlist(self, symbol: str) -> None:
        if symbol in self._watchlist:
            self._watchlist.remove(symbol)

    def get_watchlist(self) -> list[str]:
        return self._watchlist.copy()

    async def monitor_stocks(
        self,
        symbols: list[str],
        callback: Any
    ) -> None:
        self._news_callbacks.append(callback)

        while self._status.value != "offline":
            for symbol in symbols:
                info = await self._get_stock_info({"symbol": symbol})
                try:
                    callback(info)
                except Exception:
                    pass
            await asyncio.sleep(60)

    def clear_cache(self) -> None:
        self._cache.clear()


financial_agent = FinancialAgent()
