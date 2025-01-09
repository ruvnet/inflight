import { AgenticController } from './controller';
import { RealtimeLLMClient } from '../openai/realtime_client';

// Mock OpenAI client
jest.mock('../openai/realtime_client');

class MockLLMClient extends RealtimeLLMClient {
  constructor() {
    super({ apiKey: 'test-key', modalities: ['text'] });
  }

  async streamText(prompt: string): Promise<AsyncGenerator<string, void, void>> {
    const generator = async function*() {
      // Simulate streaming response based on event type
      if (prompt.includes('market')) {
        yield `Action: TRADE
Confidence: 0.85
Reasoning:
1. Strong market indicators
2. Clear upward trend
3. High volume activity
Details:
{
  "asset": "BTC",
  "action": "BUY",
  "amount": 0.5,
  "price": 45000
}`;
      } else if (prompt.includes('code')) {
        yield `Action: UPDATE
Confidence: 0.95
Reasoning:
1. Syntax error detected
2. Clear fix available
3. Low risk change
Details:
{
  "file": "main.ts",
  "line": 42,
  "fix": "Add missing semicolon"
}`;
      } else {
        yield `Action: NO_ACTION
Confidence: 0.3
Reasoning:
1. Insufficient data
2. Unclear context
3. Low confidence in analysis
Details:
{
  "reason": "Need more information"
}`;
      }
    };
    return generator();
  }
}

describe('AgenticController', () => {
  let llmClient: MockLLMClient;
  let controller: AgenticController;

  beforeEach(() => {
    llmClient = new MockLLMClient();
    controller = new AgenticController(llmClient);
  });

  it('processes market events', async () => {
    const event = {
      type: 'market',
      timestamp: new Date().toISOString(),
      data: {
        asset: 'BTC',
        price: 45000,
        volume: 100,
        indicators: {
          rsi: 65,
          macd: 1.5,
        },
      },
    };

    await controller.processEvent(event);
  });

  it('processes code events', async () => {
    const event = {
      type: 'code',
      timestamp: new Date().toISOString(),
      data: {
        file: 'main.ts',
        content: 'const x = 5',
        language: 'typescript',
      },
    };

    await controller.processEvent(event);
  });

  it('handles unknown event types', async () => {
    const event = {
      type: 'unknown',
      timestamp: new Date().toISOString(),
      data: {
        message: 'Test event',
      },
    };

    await controller.processEvent(event);
  });

  it('handles invalid events gracefully', async () => {
    // Test null event
    await expect(async () => {
      // @ts-ignore - Testing invalid input
      await controller.processEvent(null);
    }).rejects.toThrow();

    // Test empty event
    await expect(async () => {
      await controller.processEvent({});
    }).rejects.toThrow();

    // Test missing timestamp
    await expect(async () => {
      await controller.processEvent({
        type: 'test',
        data: {},
      });
    }).rejects.toThrow();

    // Test missing data
    await expect(async () => {
      await controller.processEvent({
        type: 'test',
        timestamp: new Date().toISOString(),
      });
    }).rejects.toThrow();
  });

  it('retries on temporary failures', async () => {
    let attempts = 0;
    const failingClient = new MockLLMClient();
    
    // Override streamText for this test
    failingClient.streamText = async function(prompt: string): Promise<AsyncGenerator<string, void, void>> {
      attempts++;
      if (attempts === 1) {
        throw new Error('Temporary failure');
      }
      return (async function*() {
        yield 'Action: NO_ACTION\nConfidence: 0.5\nReasoning:\n1. Test\nDetails:\n{"reason":"test"}';
      })();
    };

    const retryController = new AgenticController(failingClient);
    await retryController.processEvent({
      type: 'test',
      timestamp: new Date().toISOString(),
      data: {},
    });

    expect(attempts).toBe(2);
  });

  it('validates event format', async () => {
    const event = {
      type: 'market',
      timestamp: new Date().toISOString(),
      data: {
        asset: 'BTC',
        price: 45000,
      },
    };

    await expect(controller.processEvent(event)).resolves.not.toThrow();
  });
});
