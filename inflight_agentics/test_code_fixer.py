"""Real-time code monitoring and fixing using agentic decision making."""
import asyncio
import io
import logging
import sys
import tempfile
import traceback
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

from inflight_agentics import AgenticController

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class CodeFixerAgent:
    """Agent that monitors code execution and suggests fixes."""
    
    def __init__(self):
        """Initialize the code fixer agent."""
        self.controller = AgenticController()
        self.output_buffer = io.StringIO()
        self.error_context: Dict[str, Any] = {}
    
    @contextmanager
    def capture_output(self):
        """Capture stdout and stderr."""
        stdout, stderr = sys.stdout, sys.stderr
        try:
            sys.stdout = sys.stderr = self.output_buffer
            yield
        finally:
            sys.stdout, sys.stderr = stdout, stderr
    
    def execute_code(self, code: str) -> Dict[str, Any]:
        """Execute code and capture its output and any errors."""
        self.output_buffer.seek(0)
        self.output_buffer.truncate()
        
        try:
            with self.capture_output():
                with tempfile.NamedTemporaryFile(mode='w', suffix='.py') as temp_file:
                    temp_file.write(code)
                    temp_file.flush()
                    exec(compile(code, temp_file.name, 'exec'))
            
            output = self.output_buffer.getvalue()
            return {
                "success": True,
                "output": output,
                "error": None,
                "error_type": None,
                "error_line": None
            }
            
        except Exception as e:
            error_type = type(e).__name__
            tb = traceback.extract_tb(sys.exc_info()[2])
            error_line = tb[-1].lineno if tb else None
            error_msg = str(e)
            output = self.output_buffer.getvalue()
            
            self.error_context = {
                "error_type": error_type,
                "error_message": error_msg,
                "error_line": error_line,
                "traceback": traceback.format_exc(),
                "output": output
            }
            
            return {
                "success": False,
                "output": output,
                "error": error_msg,
                "error_type": error_type,
                "error_line": error_line
            }
    
    async def get_fix_suggestion(self, code: str, execution_result: Dict[str, Any]) -> Dict[str, Any]:
        """Get suggestions for fixing code based on execution results."""
        event = {
            "code": code,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "execution_result": execution_result,
            "error_context": self.error_context
        }
        
        if execution_result["success"]:
            event["status"] = "SUCCESS"
            event["output"] = execution_result["output"]
        else:
            event["status"] = "ERROR"
            event["error_type"] = execution_result["error_type"]
            event["error_message"] = execution_result["error"]
            event["error_line"] = execution_result["error_line"]
        
        return await self.controller.process_event(event)

def print_section(title: str, content: str = "", char: str = "=", width: int = 80):
    """Print a formatted section with title and content."""
    print(f"\n{char * width}")
    print(f"{title:^{width}}")
    print(char * width)
    if content:
        print(content.strip())
        print(char * width)

async def test_code_fixing():
    """Test the code fixing capabilities."""
    agent = CodeFixerAgent()
    
    test_cases = [
        # Case 1: Syntax Error
        {
            "name": "Missing colon in function definition",
            "code": """
def calculate_total(items)  # Missing colon
    return sum(items)

numbers = [1 2 3 4 5]  # Missing commas
print(calculate_total(numbers))
"""
        },
        
        # Case 2: Type Error
        {
            "name": "Type mismatch in operation",
            "code": """
def process_data(data):
    return data + 10  # Trying to add int to list without type check

items = [1, 2, 3]
result = process_data(items)
print(result)
"""
        },
        
        # Case 3: Name Error
        {
            "name": "Undefined variable",
            "code": """
def update_config(settings):
    config.update(settings)  # config not defined
    return config

result = update_config({"debug": True})
print(result)
"""
        },

        # Case 4: Indentation Error
        {
            "name": "Incorrect indentation",
            "code": """
def calculate_average(numbers):
    total = 0
for num in numbers:  # Wrong indentation
    total += num
    count = len(numbers)
    return total / count

avg = calculate_average([1, 2, 3, 4, 5])
print(avg)
"""
        },

        # Case 5: Logic Error
        {
            "name": "Division by zero possibility",
            "code": """
def safe_divide(x, y):
    return x / y  # Missing zero check

result = safe_divide(10, 0)
print(result)
"""
        }
    ]
    
    try:
        for i, test_case in enumerate(test_cases, 1):
            print_section(f"Test Case {i}: {test_case['name']}")
            
            # Show original code
            print_section("Original Code", test_case['code'], char="-")
            
            # Execute the code
            result = agent.execute_code(test_case['code'])
            
            # Show execution results
            status = "✓ SUCCESS" if result['success'] else "✗ FAILED"
            execution_info = []
            if result['error']:
                execution_info.extend([
                    f"Error Type: {result['error_type']}",
                    f"Error Message: {result['error']}",
                    f"Error Line: {result['error_line']}"
                ])
            if result['output']:
                execution_info.append(f"Output: {result['output']}")
            
            print_section("Execution Result", 
                         f"{status}\n" + "\n".join(execution_info), 
                         char="-")
            
            # Get and show fix suggestions if there was an error
            if not result['success']:
                fix = await agent.get_fix_suggestion(test_case['code'], result)
                
                # Show the structured fix information
                if fix['action_type'] == "FIX":
                    print_section("Analysis", fix['details']['analysis'], char="-")
                    print_section("Solution", fix['details']['solution'], char="-")
                    print_section("Explanation", fix['details']['explanation'], char="-")
                    print_section("Best Practices", fix['details']['best_practices'], char="-")
                    print_section("Confidence", f"{fix['confidence'] * 100:.1f}%", char="-")
            
    except KeyboardInterrupt:
        print_section("Test interrupted by user")
    except Exception as e:
        logger.error(f"Error during test: {e}")
        raise
    finally:
        print_section("Test completed")

if __name__ == "__main__":
    print_section("Starting Code Fixer Test")
    asyncio.run(test_code_fixing())
    print_section("All tests completed")
