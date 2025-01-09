import { EventConsumer, EventHandler } from './consumer';
import { EventProducer } from './producer';

class TestEventHandler implements EventHandler {
  public events: Record<string, unknown>[] = [];

  async processEvent(event: Record<string, unknown>): Promise<void> {
    this.events.push(event);
  }
}

describe('EventConsumer', () => {
  const redisUrl = process.env.REDIS_URL ?? 'redis://localhost:6379';
  const handler = new TestEventHandler();
  let consumer: EventConsumer;
  let producer: EventProducer;

  beforeEach(async () => {
    consumer = new EventConsumer(redisUrl, handler);
    producer = new EventProducer(redisUrl);
    await Promise.all([
      consumer.connect(),
      producer.connect(),
    ]);
  });

  afterEach(async () => {
    await Promise.all([
      consumer.disconnect(),
      producer.disconnect(),
    ]);
  });

  it('subscribes to channels and receives events', async () => {
    // Start subscription
    await consumer.subscribe(['test-channel']);

    // Wait for subscription to be established
    await new Promise(resolve => setTimeout(resolve, 100));

    // Publish test events
    const testEvents = [
      {
        type: 'test-1',
        timestamp: new Date().toISOString(),
        data: { message: 'Hello' },
      },
      {
        type: 'test-2',
        timestamp: new Date().toISOString(),
        data: { message: 'World' },
      },
    ];

    for (const event of testEvents) {
      await producer.publishEvent('test-channel', event);
    }

    // Wait for events to be processed
    await new Promise(resolve => setTimeout(resolve, 100));

    // Verify events were received
    expect(handler.events).toHaveLength(testEvents.length);
    expect(handler.events[0].type).toBe(testEvents[0].type);
    expect(handler.events[1].type).toBe(testEvents[1].type);
  });

  it('handles connection errors gracefully', async () => {
    const invalidConsumer = new EventConsumer('redis://invalid:1234', handler);
    await expect(invalidConsumer.connect()).rejects.toThrow();
  });

  it('handles subscription errors gracefully', async () => {
    const errorHandler = new class implements EventHandler {
      async processEvent(): Promise<void> {
        throw new Error('Simulated processing error');
      }
    }();

    const errorConsumer = new EventConsumer(redisUrl, errorHandler);
    await errorConsumer.connect();

    // Subscribe and publish an event that will cause an error
    await errorConsumer.subscribe(['error-channel']);
    await producer.publishEvent('error-channel', { type: 'error-test' });

    // Wait for event to be processed
    await new Promise(resolve => setTimeout(resolve, 100));

    // Clean up
    await errorConsumer.disconnect();
  });

  it('handles multiple subscriptions', async () => {
    const channels = ['channel-1', 'channel-2', 'channel-3'];
    await consumer.subscribe(channels);

    // Wait for subscriptions to be established
    await new Promise(resolve => setTimeout(resolve, 100));

    // Publish to each channel
    for (const channel of channels) {
      await producer.publishEvent(channel, {
        type: 'multi-test',
        channel,
        timestamp: new Date().toISOString(),
      });
    }

    // Wait for events to be processed
    await new Promise(resolve => setTimeout(resolve, 100));

    // Verify events from all channels were received
    expect(handler.events).toHaveLength(channels.length);
    channels.forEach((channel, index) => {
      expect(handler.events[index].channel).toBe(channel);
    });
  });
});
