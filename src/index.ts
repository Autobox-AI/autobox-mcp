#!/usr/bin/env node

import { AutoboxMCPServer } from './mcp/index.js';
import { logger } from './utils/logger.js';

async function main(): Promise<void> {
  try {
    const server = new AutoboxMCPServer();
    await server.run();
  } catch (error) {
    logger.error('Fatal error:', error);
    process.exit(1);
  }
}

main();
