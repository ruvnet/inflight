"""Core agentic logic for processing flight events and code fixes."""
import logging
import re
from typing import Dict, Any, Optional, List, Tuple

from inflight_agentics.openai_realtime_integration import RealtimeLLMClient
from inflight_agentics.config.settings import LOG_LEVEL

logging.basicConfig(level=LOG_LEVEL)
logger = logging.getLogger(__name__)

class AgenticController:
    """Controller for processing events using agentic logic and LLM integration."""

    def __init__(self, llm_client: Optional[RealtimeLLMClient] = None):
        """Initialize the controller."""
        self.llm_client = llm_client or RealtimeLLMClient()
        logger.info("Agentic Controller initialized with RealtimeLLMClient.")

    async def process_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Process an event using agentic logic."""
        if "code" in event:
            return await self._handle_code_event(event)
        elif "market_data" in event:
            return await self._handle_market_event(event)
        elif "flight_id" in event:
            return await self._handle_flight_event(event)
        else:
            return self._error_response("Unknown event type")

    async def _handle_market_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Handle market-related events."""
        market_data = event.get("market_data", {})
        portfolio = event.get("portfolio", {})
        
        if not market_data:
            return self._error_response("Missing market data")

        prompt = self._generate_market_prompt(event)
        
        try:
            llm_response = await self.llm_client.stream_text(prompt)
            action = self._parse_market_response(llm_response, market_data)
            
            logger.info(f"Determined action for {market_data['asset']}: {action['action_type']}")
            return action

        except Exception as e:
            logger.error(f"Error during market analysis: {e}")
            return self._error_response(str(e))

    def _generate_market_prompt(self, event: Dict[str, Any]) -> str:
        """Generate a prompt for market events."""
        market_data = event["market_data"]
        portfolio = event["portfolio"]
        
        prompt = (
            f"Analyze the following market conditions for {market_data['asset']}:\n\n"
            f"Price: ${market_data['price']:,.2f}\n"
            f"Volume: {market_data['volume']}\n"
            f"RSI: {market_data['indicators']['rsi']}\n"
            f"MACD Value: {market_data['indicators']['macd']['value']}\n"
            f"MACD Signal: {market_data['indicators']['macd']['signal']}\n"
            f"MACD Histogram: {market_data['indicators']['macd']['histogram']}\n"
            f"Sentiment Score: {market_data['indicators']['sentiment_score']}\n"
            f"Market Trend: {market_data['market_context']['trend']}\n"
            f"Volatility: {market_data['market_context']['volatility']}\n"
            f"News Sentiment: {market_data['market_context']['news_sentiment']}\n\n"
            f"Current Portfolio:\n"
        )
        
        for asset, amount in portfolio.items():
            prompt += f"{asset}: {float(amount):,.2f}\n"
        
        prompt += (
            "\nBased on this information, what trading action should be taken? "
            "Consider technical indicators, market sentiment, and risk management. "
            "Provide a structured response with:\n"
            "1. Action (BUY/SELL/HOLD)\n"
            "2. Size (if BUY/SELL)\n"
            "3. Reasoning\n"
            "4. Risk assessment\n"
            "5. Confidence level"
        )
        
        return prompt

    def _parse_market_response(self, response: str, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse LLM response for market events."""
        try:
            response_lower = response.lower()
            steps = self._extract_steps(response)
            
            # Extract action from the numbered list, handling various formats
            action_match = re.search(r'(?:1\.|Action:?)\s*\**(?:Action:?)?\**:?\s*(\w+)', response, re.IGNORECASE)
            if action_match:
                action_type = action_match.group(1).upper()
            else:
                action_type = "HOLD"
            
            # Extract suggested size if present, handling various formats
            suggested_size = 0.0
            
            # Try to find percentage-based size
            percent_match = re.search(r'size:?\s*(?:approximately|about|~)?\s*(?:allocate\s*)?([\d.]+)(?:\s*%|\s*percent(?:age)?)', response_lower)
            if percent_match:
                suggested_size = f"{float(percent_match.group(1))}%"
            else:
                # Try to find absolute size with various formats
                size_pattern = r'(?:size:?\s*|buy\s+|sell\s+)(?:approximately|about|~|an?\s+additional|consider\s+(?:buying|selling))?\s*([\d.]+)\s*(?:btc|eth|coins?)?'
                abs_match = re.search(size_pattern, response_lower, re.IGNORECASE)
                if abs_match:
                    suggested_size = float(abs_match.group(1))
                else:
                    # Try to find range-based size and take the average
                    range_match = re.search(r'size:?\s*(?:between|around|about)?\s*([\d.]+)(?:\s*-\s*|\s*to\s*)([\d.]+)', response_lower)
                    if range_match:
                        min_val = float(range_match.group(1))
                        max_val = float(range_match.group(2))
                        suggested_size = (min_val + max_val) / 2
            
            # Determine confidence
            confidence = self._determine_confidence(response)
            
            return {
                "action_type": action_type,
                "details": {
                    "asset": market_data["asset"],
                    "price": market_data["price"],
                    "size": suggested_size,
                    "raw_response": response
                },
                "confidence": confidence,
                "reasoning": response,
                "steps": steps
            }

        except Exception as e:
            logger.error(f"Error parsing market response: {e}")
            return self._error_response("Failed to parse market response")

    async def _handle_code_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Handle code-related events."""
        code = event.get("code", "")
        execution_result = event.get("execution_result", {})
        error_context = event.get("error_context", {})

        if not code:
            return self._error_response("No code provided")

        prompt = self._generate_code_prompt(code, execution_result, error_context)

        try:
            llm_response = await self.llm_client.stream_text(prompt)
            action = self._parse_code_fix_response(llm_response)
            
            logger.info(f"Determined fix action: {action['action_type']}")
            return action

        except Exception as e:
            logger.error(f"Error during code fix processing: {e}")
            return self._error_response(str(e))

    def _generate_code_prompt(
        self, code: str, execution_result: Dict[str, Any], error_context: Dict[str, Any]
    ) -> str:
        """Generate a prompt for code fixing."""
        prompt = (
            "As a Python expert, analyze this code and provide a detailed fix. "
            "Format your response in clear sections:\n\n"
        )

        # Add code context
        prompt += f"CODE TO FIX:\n```python\n{code}\n```\n\n"

        # Add error context if present
        if not execution_result.get("success"):
            prompt += (
                "ERROR DETAILS:\n"
                f"- Type: {error_context.get('error_type')}\n"
                f"- Message: {error_context.get('error_message')}\n"
                f"- Line: {error_context.get('error_line')}\n"
                f"- Traceback:\n{error_context.get('traceback')}\n\n"
            )

        # Add output context if present
        if output := execution_result.get("output"):
            prompt += f"OUTPUT:\n{output}\n\n"

        # Request structured response
        prompt += (
            "Please provide a detailed analysis and fix in the following format:\n\n"
            "1. ISSUE ANALYSIS\n"
            "   Explain what's wrong with the code\n\n"
            "2. SOLUTION\n"
            "   Provide the corrected code with explanations\n\n"
            "3. EXPLANATION\n"
            "   Explain why the fix works\n\n"
            "4. BEST PRACTICES\n"
            "   List specific practices to prevent similar issues\n\n"
            "Make your response clear and actionable."
        )

        return prompt

    async def _handle_flight_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Handle flight-related events."""
        flight_id = event.get("flight_id")
        status = event.get("status")
        timestamp = event.get("timestamp")

        if not all([flight_id, status, timestamp]):
            return self._error_response("Missing required flight event fields")

        prompt = self._generate_flight_prompt(event)
        
        try:
            llm_response = await self.llm_client.stream_text(prompt)
            action = self._parse_flight_response(llm_response)
            
            logger.info(f"Determined action for {flight_id}: {action['action_type']}")
            return action

        except Exception as e:
            logger.error(f"Error during flight event processing: {e}")
            return self._error_response(str(e))

    def _generate_flight_prompt(self, event: Dict[str, Any]) -> str:
        """Generate a prompt for flight events."""
        prompt = (
            f"Flight {event['flight_id']} is currently {event['status']} "
            f"as of {event['timestamp']}. "
        )

        if "delay_minutes" in event:
            prompt += f"The flight is delayed by {event['delay_minutes']} minutes. "
        if "reason" in event:
            prompt += f"The reason given is: {event['reason']}. "

        prompt += (
            "Based on this information, what action should be taken? "
            "Consider passenger impact, operational constraints, and airline policies. "
            "Respond with a structured decision including action type, specific details, "
            "confidence level, and reasoning. List specific steps that should be taken."
        )

        return prompt

    def _parse_code_fix_response(self, response: str) -> Dict[str, Any]:
        """Parse LLM response for code fixes."""
        try:
            # Extract sections using regex
            sections = {
                "ISSUE ANALYSIS": "",
                "SOLUTION": "",
                "EXPLANATION": "",
                "BEST PRACTICES": ""
            }
            
            current_section = None
            for line in response.split("\n"):
                for section in sections:
                    if section in line.upper():
                        current_section = section
                        continue
                if current_section and line.strip():
                    sections[current_section] += line + "\n"

            # Extract steps from the solution section
            steps = self._extract_steps(sections["SOLUTION"])
            
            # Determine confidence based on language used
            confidence = self._determine_confidence(response)

            return {
                "action_type": "FIX",
                "details": {
                    "analysis": sections["ISSUE ANALYSIS"].strip(),
                    "solution": sections["SOLUTION"].strip(),
                    "explanation": sections["EXPLANATION"].strip(),
                    "best_practices": sections["BEST PRACTICES"].strip()
                },
                "confidence": confidence,
                "reasoning": response,
                "steps": steps
            }

        except Exception as e:
            logger.error(f"Error parsing code fix response: {e}")
            return self._error_response("Failed to parse fix suggestion")

    def _parse_flight_response(self, response: str) -> Dict[str, Any]:
        """Parse LLM response for flight events."""
        try:
            response_lower = response.lower()
            steps = self._extract_steps(response)
            action_type, confidence = self._determine_action_and_confidence(
                response_lower, steps[0] if steps else ""
            )

            return {
                "action_type": action_type,
                "details": {
                    "raw_response": response,
                    "num_steps": len(steps)
                },
                "confidence": confidence,
                "reasoning": response,
                "steps": steps
            }

        except Exception as e:
            logger.error(f"Error parsing flight response: {e}")
            return self._error_response("Failed to parse response")

    def _extract_steps(self, response: str) -> List[str]:
        """Extract numbered steps from the response."""
        steps = re.findall(r'\d+\.\s+([^\n]+)', response)
        return [step.strip() for step in steps]

    def _determine_confidence(self, response: str) -> float:
        """Determine confidence level based on language used."""
        response_lower = response.lower()
        
        high_confidence = [
            "definitely", "certainly", "clearly", "obvious", "must", 
            "essential", "critical", "always", "fundamental"
        ]
        medium_confidence = [
            "should", "recommend", "suggest", "typically", "generally",
            "usually", "often", "common"
        ]
        low_confidence = [
            "might", "may", "could", "possibly", "perhaps", "consider",
            "maybe", "uncertain", "unclear", "try"
        ]

        if any(word in response_lower for word in high_confidence):
            return 0.9
        elif any(word in response_lower for word in low_confidence):
            return 0.5
        elif any(word in response_lower for word in medium_confidence):
            return 0.7
        
        return 0.6  # Default confidence

    def _determine_action_and_confidence(
        self, response: str, first_step: str
    ) -> Tuple[str, float]:
        """Determine the primary action type and confidence level."""
        action_type = "MONITOR"
        confidence = 0.7

        action_keywords = {
            "REBOOK": ["rebook", "alternative", "reschedule"],
            "NOTIFY": ["notify", "inform", "communicate", "alert"],
            "CANCEL": ["cancel"],
            "MONITOR": ["monitor", "observe", "track"]
        }

        first_step_lower = first_step.lower()
        for action, keywords in action_keywords.items():
            if any(keyword in first_step_lower for keyword in keywords):
                action_type = action
                break
            elif any(keyword in response for keyword in keywords):
                action_type = action

        confidence = self._determine_confidence(response)
        return action_type, confidence

    def _error_response(self, error_msg: str) -> Dict[str, Any]:
        """Generate an error response."""
        return {
            "action_type": "ERROR",
            "details": {"error": error_msg},
            "confidence": 0.0,
            "reasoning": error_msg,
            "steps": []
        }

    def __repr__(self) -> str:
        """Return string representation of the controller."""
        return f"AgenticController(llm_client={self.llm_client})"
