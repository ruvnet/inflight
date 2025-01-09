import { RealtimeLLMClient } from "./openai/realtime_client.ts";
import { AgenticController } from "./agentic/controller.ts";
import { EventConsumer } from "./queue/consumer.ts";
import { EventProducer } from "./queue/producer.ts";

async function main() {
  try {
    // Initialize OpenAI client
    const llmClient = new RealtimeLLMClient({
      apiKey: process.env.OPENAI_API_KEY ?? '',
      modalities: ['text'],
      maxRetries: parseInt(process.env.MAX_RETRIES ?? '3'),
      retryDelay: parseInt(process.env.RETRY_DELAY ?? '1000'),
    });

    // Initialize agentic controller
    const controller = new AgenticController(llmClient);

    // Initialize event producer and consumer
    const redisUrl = process.env.REDIS_URL ?? 'redis://localhost:6379';
    const producer = new EventProducer(redisUrl);
    const consumer = new EventConsumer(redisUrl, controller);

    // Connect to Redis
    await Promise.all([
      producer.connect(),
      consumer.connect(),
    ]);

    // Subscribe to channels
    const channels = (process.env.REDIS_CHANNELS ?? 'market-events,code-events').split(',');
    await consumer.subscribe(channels);

    console.log('Inflight System running...');
    console.log('Subscribed to channels:', channels);

    // Handle shutdown
    process.on('SIGINT', async () => {
      console.log('\nShutting down...');
      await Promise.all([
        producer.disconnect(),
        consumer.disconnect(),
      ]);
      process.exit(0);
    });

  } catch (error) {
    console.error('Failed to start system:', error);
    process.exit(1);
  }
}

main();
