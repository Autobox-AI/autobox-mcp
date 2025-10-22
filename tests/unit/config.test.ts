import { ConfigManager } from '../../src/config/paths';
import { existsSync, mkdirSync, writeFileSync, unlinkSync } from 'fs';
import { join } from 'path';
import { tmpdir } from 'os';

describe('ConfigManager', () => {
  let configManager: ConfigManager;
  let testDir: string;

  beforeEach(() => {
    testDir = join(tmpdir(), `autobox-test-${Date.now()}`);
    mkdirSync(testDir, { recursive: true });

    configManager = new ConfigManager(testDir);
  });

  afterEach(() => {
    if (existsSync(testDir)) {
      const rimraf = (dir: string) => {
        if (existsSync(dir)) {
          const { readdirSync, statSync, rmdirSync } = require('fs');
          readdirSync(dir).forEach((file: string) => {
            const curPath = join(dir, file);
            if (statSync(curPath).isDirectory()) {
              rimraf(curPath);
            } else {
              unlinkSync(curPath);
            }
          });
          rmdirSync(dir);
        }
      };
      rimraf(testDir);
    }
  });

  describe('listAvailableConfigs', () => {
    it('should return empty array when no configs exist', () => {
      const configs = configManager.listAvailableConfigs();
      expect(configs).toEqual([]);
    });

    it('should list available simulation configs', () => {
      const simulationsPath = configManager.getSimulationsPath();
      mkdirSync(simulationsPath, { recursive: true });

      writeFileSync(join(simulationsPath, 'test1.json'), '{}');
      writeFileSync(join(simulationsPath, 'test2.json'), '{}');
      writeFileSync(join(simulationsPath, 'ignore.txt'), 'not a config');

      const configs = configManager.listAvailableConfigs();

      expect(configs).toHaveLength(2);
      expect(configs).toContain('test1');
      expect(configs).toContain('test2');
      expect(configs).not.toContain('ignore');
    });
  });

  describe('saveSimulationConfig', () => {
    it('should save simulation config', () => {
      const config = {
        name: 'test-simulation',
        description: 'Test simulation',
        task: 'Test task',
        timeout_seconds: 300,
        shutdown_grace_period_seconds: 5,
        evaluator: { name: 'EVALUATOR', llm: { model: 'gpt-4o-mini' }, context: '' },
        reporter: { name: 'REPORTER', llm: { model: 'gpt-4o-mini' }, context: '' },
        planner: { name: 'PLANNER', llm: { model: 'gpt-4o-mini' }, context: '' },
        orchestrator: { name: 'ORCHESTRATOR', llm: { model: 'gpt-4o-mini' }, context: '' },
        workers: [],
        logging: {
          verbose: false,
          log_path: 'logs',
          log_file: 'test.log',
        },
      };

      const path = configManager.saveSimulationConfig(config);

      expect(existsSync(path)).toBe(true);
      expect(path).toContain('test-simulation.json');
    });
  });

  describe('deleteSimulation', () => {
    it('should delete simulation files', () => {
      const simulationsPath = configManager.getSimulationsPath();
      const metricsPath = configManager.getMetricsPath();

      mkdirSync(simulationsPath, { recursive: true });
      mkdirSync(metricsPath, { recursive: true });

      const configFile = join(simulationsPath, 'test.json');
      const metricsFile = join(metricsPath, 'test.json');

      writeFileSync(configFile, '{}');
      writeFileSync(metricsFile, '[]');

      const result = configManager.deleteSimulation('test');

      expect(result.deleted_files).toHaveLength(2);
      expect(result.errors).toHaveLength(0);
      expect(existsSync(configFile)).toBe(false);
      expect(existsSync(metricsFile)).toBe(false);
    });
  });
});
