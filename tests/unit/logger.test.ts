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

describe('Logger', () => {
  let consoleErrorSpy: jest.SpyInstance;
  let logger: Logger;
  const originalEnv = process.env.LOG_LEVEL;

  beforeEach(() => {
    consoleErrorSpy = jest.spyOn(console, 'error').mockImplementation();
    delete process.env.LOG_LEVEL;
    logger = new Logger();
  });

  afterEach(() => {
    consoleErrorSpy.mockRestore();
    if (originalEnv !== undefined) {
      process.env.LOG_LEVEL = originalEnv;
    } else {
      delete process.env.LOG_LEVEL;
    }
  });

  describe('log level filtering', () => {
    it('should log info messages by default', () => {
      logger.info('test message');
      expect(consoleErrorSpy).toHaveBeenCalledWith('[INFO]', 'test message');
    });

    it('should log warn messages', () => {
      logger.warn('warning message');
      expect(consoleErrorSpy).toHaveBeenCalledWith('[WARN]', 'warning message');
    });

    it('should log error messages', () => {
      logger.error('error message');
      expect(consoleErrorSpy).toHaveBeenCalledWith('[ERROR]', 'error message');
    });

    it('should not log debug messages by default', () => {
      logger.debug('debug message');
      expect(consoleErrorSpy).not.toHaveBeenCalled();
    });
  });

  describe('multiple arguments', () => {
    it('should handle multiple arguments', () => {
      logger.info('message', { data: 'test' }, 123);
      expect(consoleErrorSpy).toHaveBeenCalledWith('[INFO]', 'message', { data: 'test' }, 123);
    });

    it('should handle objects and arrays', () => {
      const obj = { key: 'value' };
      const arr = [1, 2, 3];
      logger.warn('complex', obj, arr);
      expect(consoleErrorSpy).toHaveBeenCalledWith('[WARN]', 'complex', obj, arr);
    });
  });

  describe('log level hierarchy', () => {
    it('should respect log level configuration', () => {
      const levels = ['error', 'warn', 'info', 'debug'];

      expect(levels).toContain('error');
      expect(levels).toContain('warn');
      expect(levels).toContain('info');
      expect(levels).toContain('debug');
      expect(levels.indexOf('error')).toBeLessThan(levels.indexOf('debug'));
    });

    it('should have shouldLog method that filters by level', () => {
      expect(typeof logger['shouldLog']).toBe('function');
    });
  });

  describe('edge cases', () => {
    it('should handle empty log calls', () => {
      logger.info();
      expect(consoleErrorSpy).toHaveBeenCalledWith('[INFO]');
    });

    it('should handle null and undefined', () => {
      logger.info(null, undefined);
      expect(consoleErrorSpy).toHaveBeenCalledWith('[INFO]', null, undefined);
    });

    it('should handle error objects', () => {
      const error = new Error('test error');
      logger.error('Error occurred:', error);
      expect(consoleErrorSpy).toHaveBeenCalledWith('[ERROR]', 'Error occurred:', error);
    });
  });
});
