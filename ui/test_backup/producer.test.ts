import { jest, describe, beforeEach, afterEach, it, expect } from '@jest/globals';
import { EventProducer } from './producer';
import IORedis from 'ioredis';

type MockRedisInstance = {
  ping: jest.MockedFunction<() => Promise<'PONG'>>;
  publish: jest.MockedFunction<(channel: string, message: string) => Promise<number>>;
  quit: jest.MockedFunction<() => Promise<'OK'>>;
};

// Mock the Redis constructor
jest.mock('ioredis', () => {
  return jest.fn().mockImplementation(() => ({
    ping: jest.fn().mockResolvedValue('PONG'),
    publish: jest.fn().mockResolvedValue(1),
    quit: jest.fn().mockResolvedValue('OK'),
  }));
});

describe('EventProducer', () => {
  const redisUrl = 'redis://localhost:6379';
  let producer: EventProducer;
  let mockRedis: MockRedisInstance;

  beforeEach(() => {
    // Clear all mocks
    producer = new EventProducer(redisUrl);
    // Get the mock instance
    const MockRedisConstructor = jest.mocked(IORedis);
    mockRedis = MockRedisConstructor.mock.results[0]?.value;
  });

  afterEach(async () => {
    await producer.disconnect();
  });

  it('connects to Redis successfully', async () => {
    await expect(producer.connect()).resolves.not.toThrow();
    expect(mockRedis.ping).toHaveBeenCalled();
  });

  it('publishes events', async () => {
    await producer.connect();
    const event = {
      type: 'test',
      timestamp: new Date().toISOString(),
      data: {
        message: 'Hello, World!',
      },
    };

    await producer.publishEvent('test-channel', event);
    expect(mockRedis.publish).toHaveBeenCalledWith('test-channel', JSON.stringify(event));
  });

  it('handles connection errors gracefully', async () => {
    const errorMessage = 'Connection failed';
    // Override the ping implementation for this test
    mockRedis.ping.mockRejectedValueOnce(new Error(errorMessage));

    await expect(producer.connect()).rejects.toThrow(errorMessage);
  });

  it('handles multiple connect/disconnect cycles', async () => {
    for (let i = 0; i < 3; i++) {
      await producer.connect();
      await producer.publishEvent('test-channel', {
        type: 'cycle-test',
        iteration: i,
      });
      await producer.disconnect();
    }

    expect(mockRedis.ping).toHaveBeenCalledTimes(3);
    expect(mockRedis.quit).toHaveBeenCalledTimes(3);
  });

  it('validates event data', async () => {
    await producer.connect();

    // Test null event
    await expect(async () => {
      // @ts-ignore - Testing invalid input
      await producer.publishEvent('test-channel', null);
    }).rejects.toThrow();

    // Test missing channel
    await expect(async () => {
      // @ts-ignore - Testing invalid input
      await producer.publishEvent(null, { type: 'test' });
    }).rejects.toThrow();
  });

  it('handles disconnection when not connected', async () => {
    await expect(producer.disconnect()).resolves.not.toThrow();
    expect(mockRedis?.quit).not.toHaveBeenCalled();
  });

  it('handles publishing when not connected', async () => {
    await expect(producer.publishEvent('test-channel', { type: 'test' }))
      .rejects.toThrow('Redis client not connected');
    expect(mockRedis?.publish).not.toHaveBeenCalled();
  });
});
