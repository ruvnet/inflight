// External dependencies
import WebSocket from 'npm:ws';
import { connect } from "https://deno.land/x/redis@v0.32.1/mod.ts";
import { Decimal } from 'npm:decimal.js';

// Export dependencies
export {
  WebSocket,
  connect as Redis,
  Decimal,
};

// Export Redis types
export type { Redis as RedisType } from "https://deno.land/x/redis@v0.32.1/mod.ts";

// Test utilities from Deno
export { assertEquals, assertExists } from "https://deno.land/std@0.208.0/assert/mod.ts";
