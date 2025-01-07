"""Real-time market monitoring and trading using agentic decision making."""
import logging
import sys
from datetime import datetime, timezone
from typing import Dict, Any, List
from decimal import Decimal

from inflight_agentics import AgenticController

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class TradingAgent:
    """Agent that monitors market conditions and makes trading decisions."""
    
    def __init__(self):
        """Initialize the trading agent."""
        self.controller = AgenticController()
        self.portfolio = {
            "BTC": Decimal("1.0"),
            "USD": Decimal("50000.0"),
            "ETH": Decimal("10.0")
        }
        self.trade_history: List[Dict[str, Any]] = []
    
    async def analyze_market(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze market conditions and determine trading action."""
        event = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "market_data": market_data,
            "portfolio": self.portfolio,
            "trade_history": self.trade_history
        }
        
        decision = await self.controller.process_event(event)
        
        if decision["action_type"] in ["BUY", "SELL"]:
            self._execute_trade(decision)
            
        return decision
    
    def _execute_trade(self, decision: Dict[str, Any]) -> None:
        """Simulate trade execution and update portfolio."""
        asset = decision["details"]["asset"]
        action = decision["action_type"]
        price = Decimal(str(decision["details"]["price"]))
        
        # Calculate actual size based on the suggested size and available assets
        raw_size = str(decision["details"]["size"])
        try:
            if "%" in raw_size:
                # Handle percentage-based sizes
                percentage = Decimal(raw_size.rstrip("%")) / Decimal("100")
                if action == "BUY":
                    available_usd = self.portfolio["USD"]
                    size = (available_usd * percentage) / price
                else:  # SELL
                    available_asset = self.portfolio.get(asset, Decimal("0"))
                    size = available_asset * percentage
            else:
                # Handle absolute sizes
                size = Decimal(raw_size)
        except (ValueError, TypeError):
            logger.error(f"Failed to parse trade size: {raw_size}")
            return
        
        if action == "BUY":
            cost = size * price
            if self.portfolio["USD"] >= cost:
                self.portfolio["USD"] -= cost
                self.portfolio[asset] = self.portfolio.get(asset, Decimal("0")) + size
                self.trade_history.append({
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "action": "BUY",
                    "asset": asset,
                    "size": float(size),
                    "price": float(price),
                    "cost": float(cost)
                })
        elif action == "SELL":
            if self.portfolio.get(asset, Decimal("0")) >= size:
                proceeds = size * price
                self.portfolio[asset] -= size
                self.portfolio["USD"] += proceeds
                self.trade_history.append({
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "action": "SELL",
                    "asset": asset,
                    "size": float(size),
                    "price": float(price),
                    "proceeds": float(proceeds)
                })

def print_section(title: str, content: str = "", char: str = "=", width: int = 80):
    """Print a formatted section with title and content."""
    print(f"\n{char * width}")
    print(f"{title:^{width}}")
    print(char * width)
    if content:
        print(content.strip())
        print(char * width)

def format_market_data(data: Dict[str, Any]) -> str:
    """Format market data for display."""
    lines = [
        f"Asset: {data['asset']}",
        f"Price: ${data['price']:,.2f}",
        f"Volume: {data['volume']:,.2f}",
        f"RSI: {data['indicators']['rsi']:.1f}",
        f"MACD Value: {data['indicators']['macd']['value']:.1f}",
        f"MACD Signal: {data['indicators']['macd']['signal']:.1f}",
        f"MACD Histogram: {data['indicators']['macd']['histogram']:.1f}",
        f"Sentiment Score: {data['indicators']['sentiment_score']:.2f}",
        f"Trend: {data['market_context']['trend']}",
        f"Volatility: {data['market_context']['volatility']}",
        f"News Sentiment: {data['market_context']['news_sentiment']}"
    ]
    return "\n".join(lines)

def format_portfolio(portfolio: Dict[str, Decimal]) -> str:
    """Format portfolio for display."""
    lines = [f"{asset}: {float(amount):,.2f}" for asset, amount in portfolio.items()]
    return "\n".join(lines)

async def test_trading_agent():
    """Test the trading decision capabilities."""
    agent = TradingAgent()
    
    test_cases = [
        # Case 1: Strong Buy Signal
        {
            "name": "Bullish Market Conditions",
            "market_data": {
                "asset": "BTC",
                "price": 42150.75,
                "volume": 2.5,
                "indicators": {
                    "rsi": 65.5,
                    "macd": {
                        "value": 145.2,
                        "signal": 132.8,
                        "histogram": 12.4
                    },
                    "sentiment_score": 0.82
                },
                "market_context": {
                    "volatility": "medium",
                    "trend": "bullish",
                    "news_sentiment": "positive"
                }
            }
        },
        
        # Case 2: Strong Sell Signal
        {
            "name": "Overbought Conditions",
            "market_data": {
                "asset": "BTC",
                "price": 44500.00,
                "volume": 3.2,
                "indicators": {
                    "rsi": 78.5,
                    "macd": {
                        "value": 155.2,
                        "signal": 160.8,
                        "histogram": -5.6
                    },
                    "sentiment_score": 0.45
                },
                "market_context": {
                    "volatility": "high",
                    "trend": "bearish",
                    "news_sentiment": "negative"
                }
            }
        },
        
        # Case 3: Hold Signal
        {
            "name": "Neutral Market Conditions",
            "market_data": {
                "asset": "ETH",
                "price": 2250.25,
                "volume": 15.7,
                "indicators": {
                    "rsi": 52.3,
                    "macd": {
                        "value": 25.2,
                        "signal": 24.8,
                        "histogram": 0.4
                    },
                    "sentiment_score": 0.55
                },
                "market_context": {
                    "volatility": "low",
                    "trend": "sideways",
                    "news_sentiment": "neutral"
                }
            }
        },
        
        # Case 4: Volatile Market
        {
            "name": "High Volatility Conditions",
            "market_data": {
                "asset": "BTC",
                "price": 41200.50,
                "volume": 5.8,
                "indicators": {
                    "rsi": 45.5,
                    "macd": {
                        "value": -85.2,
                        "signal": -65.8,
                        "histogram": -19.4
                    },
                    "sentiment_score": 0.35
                },
                "market_context": {
                    "volatility": "very_high",
                    "trend": "bearish",
                    "news_sentiment": "very_negative"
                }
            }
        },
        
        # Case 5: Strong Recovery Signal
        {
            "name": "Market Recovery Conditions",
            "market_data": {
                "asset": "ETH",
                "price": 2450.75,
                "volume": 25.3,
                "indicators": {
                    "rsi": 42.5,
                    "macd": {
                        "value": 35.2,
                        "signal": 15.8,
                        "histogram": 19.4
                    },
                    "sentiment_score": 0.88
                },
                "market_context": {
                    "volatility": "medium",
                    "trend": "bullish",
                    "news_sentiment": "very_positive"
                }
            }
        }
    ]
    
    try:
        print_section("Initial Portfolio", format_portfolio(agent.portfolio))
        
        for i, test_case in enumerate(test_cases, 1):
            print_section(f"Test Case {i}: {test_case['name']}")
            
            # Show market conditions
            print_section("Market Data", format_market_data(test_case['market_data']), char="-")
            
            # Get trading decision
            decision = await agent.analyze_market(test_case['market_data'])
            
            # Show decision details
            decision_info = [
                f"Action: {decision['action_type']}",
                f"Confidence: {decision['confidence'] * 100:.1f}%",
                f"Reasoning: {decision['reasoning']}"
            ]
            if 'details' in decision:
                for key, value in decision['details'].items():
                    decision_info.append(f"{key.title()}: {value}")
            
            print_section("Trading Decision", "\n".join(decision_info), char="-")
            
            # Show updated portfolio
            print_section("Current Portfolio", format_portfolio(agent.portfolio), char="-")
            
    except KeyboardInterrupt:
        print_section("Test interrupted by user")
    except Exception as e:
        logger.error(f"Error during test: {e}")
        raise
    finally:
        print_section("Test completed")
        
        # Show final portfolio and performance
        print_section("Final Portfolio", format_portfolio(agent.portfolio))
        
        if agent.trade_history:
            trades = "\n".join([
                f"{trade['timestamp']}: {trade['action']} {trade['size']} {trade['asset']} "
                f"@ ${trade['price']:,.2f}"
                for trade in agent.trade_history
            ])
            print_section("Trade History", trades)

if __name__ == "__main__":
    import asyncio
    print_section("Starting Trading Agent Test")
    asyncio.run(test_trading_agent())
    print_section("All tests completed")
