import { Redis, RedisType } from '../deps.ts';

export class EventProducer {
  private redis: RedisType | null = null;

  constructor(private redisUrl: string) {}

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
      this.redis = await Redis(options);

      // Test connection
      await this.redis.ping();
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : String(error);
      throw new Error(`Failed to connect to Redis: ${errorMessage}`);
    }
  }

  async publishEvent(
    channel: string,
    event: Record<string, unknown>,
  ): Promise<void> {
    if (!this.redis) {
      throw new Error("Redis client not connected");
    }

    try {
      await this.redis.publish(channel, JSON.stringify(event));
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : String(error);
      throw new Error(`Failed to publish event: ${errorMessage}`);
    }
  }

  async disconnect(): Promise<void> {
    if (this.redis) {
      try {
        await this.redis.quit();
        this.redis = null;
      } catch (error) {
        const errorMessage = error instanceof Error ? error.message : String(error);
        throw new Error(`Failed to disconnect from Redis: ${errorMessage}`);
      }
    }
  }
}
