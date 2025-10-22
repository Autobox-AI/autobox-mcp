type LogLevel = 'info' | 'warn' | 'error' | 'debug';

class Logger {
  private logLevel: LogLevel = process.env.LOG_LEVEL === 'debug' ? 'debug' : 'info';

  info(...args: unknown[]): void {
    if (this.shouldLog('info')) {
      console.error('[INFO]', ...args);
    }
  }

  warn(...args: unknown[]): void {
    if (this.shouldLog('warn')) {
      console.error('[WARN]', ...args);
    }
  }

  error(...args: unknown[]): void {
    if (this.shouldLog('error')) {
      console.error('[ERROR]', ...args);
    }
  }

  debug(...args: unknown[]): void {
    if (this.shouldLog('debug')) {
      console.error('[DEBUG]', ...args);
    }
  }

  private shouldLog(level: LogLevel): boolean {
    const levels: LogLevel[] = ['error', 'warn', 'info', 'debug'];
    const currentLevelIndex = levels.indexOf(this.logLevel);
    const requestedLevelIndex = levels.indexOf(level);
    return requestedLevelIndex <= currentLevelIndex;
  }
}

export const logger = new Logger();
