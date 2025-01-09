import { jest } from '@jest/globals';

// Set up environment variables for testing
process.env.REDIS_URL = 'redis://localhost:6379';
process.env.OPENAI_API_KEY = 'test-key';
process.env.MAX_RETRIES = '3';
process.env.RETRY_DELAY = '100';
process.env.LOG_LEVEL = 'error';

// Mock console methods to reduce noise in test output
const originalConsole = global.console;
global.console = {
  ...originalConsole,
  // Keep error logging for test debugging
  error: jest.fn(),
  // Silence info and debug logs during tests
  info: jest.fn(),
  debug: jest.fn(),
  // Keep warn for important test messages
  warn: originalConsole.warn,
};

// Mock timers
jest.useFakeTimers();

// Clean up after each test
afterEach(() => {
  jest.clearAllMocks();
  jest.clearAllTimers();
});
