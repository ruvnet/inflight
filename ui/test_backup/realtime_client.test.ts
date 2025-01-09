import { RealtimeLLMClient } from './realtime_client';
import WebSocket from 'ws';

// Mock WebSocket
jest.mock('ws');

// Custom event types to match ws library
interface WSEvent {
  type: string;
  target: WebSocket;
}

interface WSMessageEvent extends WSEvent {
  data: string;
}

interface WSErrorEvent extends WSEvent {
  error: Error;
}

interface WSCloseEvent extends WSEvent {
  code: number;
  reason: string;
}

describe('RealtimeLLMClient', () => {
  let client: RealtimeLLMClient;
  let mockWs: jest.Mocked<WebSocket>;

  beforeEach(() => {
    // Clear mocks
    jest.clearAllMocks();

    // Create mock WebSocket instance
    mockWs = {
      addEventListener: jest.fn(),
      removeEventListener: jest.fn(),
      send: jest.fn(),
      close: jest.fn(),
    } as unknown as jest.Mocked<WebSocket>;

    // Mock WebSocket constructor
    (WebSocket as unknown as jest.Mock).mockImplementation(() => mockWs);

    client = new RealtimeLLMClient({
      apiKey: 'test-key',
      modalities: ['text'],
    });
  });

  it('creates a session successfully', async () => {
    // Mock successful connection
    mockWs.addEventListener.mockImplementation((event, handler) => {
      if (event === 'open') {
        setTimeout(() => handler({ type: 'open', target: mockWs } as WSEvent), 0);
      }
    });

    await expect(client.createSession()).resolves.not.toThrow();
    expect(WebSocket).toHaveBeenCalledWith(
      'wss://api.openai.com/v1/chat/completions/stream',
      expect.any(Object)
    );
  });

  it('handles streaming text responses', async () => {
    // Mock successful connection
    mockWs.addEventListener.mockImplementation((event, handler) => {
      if (event === 'open') {
        setTimeout(() => handler({ type: 'open', target: mockWs } as WSEvent), 0);
      }
    });

    await client.createSession();

    // Mock message streaming
    mockWs.addEventListener.mockImplementation((event, handler) => {
      if (event === 'message') {
        setTimeout(() => {
          handler({
            type: 'message',
            target: mockWs,
            data: JSON.stringify({
              type: 'response.text.delta',
              text: 'Hello',
            }),
          } as WSMessageEvent);
          handler({
            type: 'message',
            target: mockWs,
            data: JSON.stringify({
              type: 'response.text.delta',
              text: ' World',
            }),
          } as WSMessageEvent);
          // Simulate stream end
          mockWs.addEventListener.mockImplementation((event, handler) => {
            if (event === 'close') {
              setTimeout(() => handler({
                type: 'close',
                target: mockWs,
                code: 1000,
                reason: 'Normal closure',
              } as WSCloseEvent), 0);
            }
          });
        }, 0);
      }
    });

    const generator = await client.streamText('Test prompt');
    const chunks: string[] = [];
    for await (const chunk of generator) {
      chunks.push(chunk);
    }

    expect(chunks).toEqual(['Hello', ' World']);
    expect(mockWs.send).toHaveBeenCalledWith(
      expect.stringContaining('Test prompt')
    );
  });

  it('handles connection errors gracefully', async () => {
    // Mock connection error
    mockWs.addEventListener.mockImplementation((event, handler) => {
      if (event === 'error') {
        setTimeout(() => handler({
          type: 'error',
          target: mockWs,
          error: new Error('Connection failed'),
        } as WSErrorEvent), 0);
      }
    });

    await expect(client.createSession()).rejects.toThrow('Connection failed');
  });

  it('handles streaming errors gracefully', async () => {
    // Mock successful connection
    mockWs.addEventListener.mockImplementation((event, handler) => {
      if (event === 'open') {
        setTimeout(() => handler({ type: 'open', target: mockWs } as WSEvent), 0);
      }
    });

    await client.createSession();

    // Mock streaming error
    mockWs.addEventListener.mockImplementation((event, handler) => {
      if (event === 'error') {
        setTimeout(() => handler({
          type: 'error',
          target: mockWs,
          error: new Error('Stream error'),
        } as WSErrorEvent), 0);
      }
    });

    const generator = await client.streamText('Test prompt');
    await expect(async () => {
      for await (const chunk of generator) {
        // Should throw before getting here
      }
    }).rejects.toThrow('Stream error');
  });

  it('cleans up resources after streaming', async () => {
    // Mock successful connection
    mockWs.addEventListener.mockImplementation((event, handler) => {
      if (event === 'open') {
        setTimeout(() => handler({ type: 'open', target: mockWs } as WSEvent), 0);
      }
    });

    await client.createSession();

    // Mock immediate stream end
    mockWs.addEventListener.mockImplementation((event, handler) => {
      if (event === 'close') {
        setTimeout(() => handler({
          type: 'close',
          target: mockWs,
          code: 1000,
          reason: 'Normal closure',
        } as WSCloseEvent), 0);
      }
    });

    const generator = await client.streamText('Test prompt');
    for await (const chunk of generator) {
      // Stream ends immediately
    }

    expect(mockWs.close).toHaveBeenCalled();
  });
});
