import { Redis, RedisType } from '../deps.ts';

export interface EventHandler {
  processEvent(event: Record<string, unknown>): Promise<void>;
}

export class EventConsumer {
  private redis: RedisType | null = null;
  private subscribeClient: RedisType | null = null;

  constructor(
    private redisUrl: string,
    private handler: EventHandler
  ) {}

  private parseRedisUrl(url: string) {
    const parsed = new URL(url);
    return {
      hostname: parsed.hostname,
      port: parsed.port ? parseInt(parsed.port) : 6379,
      username: parsed.username || undefined,
      password: parsed.password || undefined,
      db: parsed.pathname ? parseInt(parsed.pathname.slice(1)) : 0,
      tls: parsed.protocol === 'rediss:',
    };
  }

  async connect(): Promise<void> {
    try {
      const options = this.parseRedisUrl(this.redisUrl);

      // Create main Redis client
      this.redis = await Redis(options);
      await this.redis.ping();

      // Create separate client for subscriptions
      this.subscribeClient = await Redis(options);
      await this.subscribeClient.ping();
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : String(error);
      throw new Error(`Failed to connect to Redis: ${errorMessage}`);
    }
  }

  async subscribe(channels: string[]): Promise<void> {
    if (!this.subscribeClient) {
      throw new Error("Redis client not connected");
    }

    try {
      // Subscribe to channels
      for (const channel of channels) {
        await this.subscribeClient.subscribe(channel);
      }
      
      // Handle messages using psubscribe for pattern matching
      const pattern = '*';
      await this.subscribeClient.psubscribe(pattern);
      
      // Create async iterator for messages
      const pubsub = await this.subscribeClient.subscribe(...channels);
      for await (const { channel, message } of pubsub.receive()) {
        try {
          const event = JSON.parse(message);
          await this.handler.processEvent(event);
        } catch (error) {
          const errorMessage = error instanceof Error ? error.message : String(error);
          console.error(`Error processing message on channel ${channel}: ${errorMessage}`);
        }
      }
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : String(error);
      throw new Error(`Failed to subscribe to channels: ${errorMessage}`);
    }
  }

  async disconnect(): Promise<void> {
    try {
      if (this.subscribeClient) {
        await this.subscribeClient.quit();
        this.subscribeClient = null;
      }
      if (this.redis) {
        await this.redis.quit();
        this.redis = null;
      }
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : String(error);
      throw new Error(`Failed to disconnect from Redis: ${errorMessage}`);
    }
  }
}
