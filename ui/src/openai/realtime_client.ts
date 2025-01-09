import { WebSocket } from '../deps.ts';

interface LLMClientConfig {
  apiKey: string;
  modalities: string[];
  maxRetries?: number;
  retryDelay?: number;
}

interface WebSocketEvent {
  data: string | ArrayBuffer | Blob;
}

interface WebSocketErrorEvent extends Event {
  error: Error;
}

export class RealtimeLLMClient {
  private ws: WebSocket | null = null;
  private readonly config: LLMClientConfig;

  constructor(config: LLMClientConfig) {
    this.config = {
      maxRetries: 3,
      retryDelay: 1000,
      ...config,
    };
  }

  async createSession(): Promise<void> {
    return new Promise((resolve, reject) => {
      try {
        this.ws = new WebSocket('wss://api.openai.com/v1/chat/completions/stream', {
          headers: {
            'Authorization': `Bearer ${this.config.apiKey}`,
            'Content-Type': 'application/json',
          },
        });

        this.ws.addEventListener('open', () => resolve());
        this.ws.addEventListener('error', (error: WebSocketErrorEvent) => reject(error));
      } catch (error) {
        reject(error);
      }
    });
  }

  async streamText(prompt: string): Promise<AsyncGenerator<string, void, void>> {
    if (!this.ws) {
      throw new Error('WebSocket connection not established');
    }

    const ws = this.ws;
    const maxRetries = this.config.maxRetries ?? 3;
    const retryDelay = this.config.retryDelay ?? 1000;
    let retries = 0;

    return new Promise<AsyncGenerator<string, void, void>>((resolve, reject) => {
      let messageResolver: ((value: IteratorResult<string, void>) => void) | null = null;
      let messageRejecter: ((reason: unknown) => void) | null = null;

      const generator = (async function*(): AsyncGenerator<string, void, void> {
        while (true) {
          const result = await new Promise<IteratorResult<string, void>>((resolve, reject) => {
            messageResolver = resolve;
            messageRejecter = reject;
          });
          
          if (result.done) {
            return;
          }
          
          yield result.value;
        }
      })();

      // Send the prompt
      ws.send(JSON.stringify({
        messages: [{ role: 'user', content: prompt }],
        stream: true,
      }));

      // Set up message handling
      ws.addEventListener('message', (event: WebSocketEvent) => {
        try {
          const response = JSON.parse(event.data.toString());
          if (response.type === 'response.text.delta' && messageResolver) {
            messageResolver({ value: response.text, done: false });
          }
        } catch (error: unknown) {
          console.error('Error parsing message:', error);
          if (messageRejecter) {
            messageRejecter(error);
          }
        }
      });

      // Handle errors
      ws.addEventListener('error', async (error: WebSocketErrorEvent) => {
        if (retries < maxRetries) {
          retries++;
          setTimeout(async () => {
            try {
              await this.createSession();
              const newGenerator = await this.streamText(prompt);
              if (messageResolver) {
                for await (const chunk of newGenerator) {
                  messageResolver({ value: chunk, done: false });
                }
              }
            } catch (retryError: unknown) {
              if (messageRejecter) {
                messageRejecter(retryError);
              }
            }
          }, retryDelay);
        } else if (messageRejecter) {
          messageRejecter(error);
        }
      });

      // Handle close
      ws.addEventListener('close', () => {
        if (messageResolver) {
          messageResolver({ value: undefined, done: true });
        }
      });

      resolve(generator);
    });
  }

  close(): void {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }
}
