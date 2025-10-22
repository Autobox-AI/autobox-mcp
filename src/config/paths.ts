import { homedir } from 'os';
import { join } from 'path';
import { readFileSync, writeFileSync, mkdirSync, existsSync, readdirSync, unlinkSync } from 'fs';
import type { SimulationConfig } from '../types/index.js';

export class ConfigManager {
  private autoboxConfigPath: string;
  private simulationsPath: string;
  private metricsPath: string;
  private serverConfigPath: string;

  constructor(basePath?: string) {
    const base = basePath || join(homedir(), '.autobox');
    this.autoboxConfigPath = join(base, 'config');
    this.simulationsPath = join(this.autoboxConfigPath, 'simulations');
    this.metricsPath = join(this.autoboxConfigPath, 'metrics');
    this.serverConfigPath = join(this.autoboxConfigPath, 'server.json');
  }

  getSimulationsPath(): string {
    return this.simulationsPath;
  }

  getMetricsPath(): string {
    return this.metricsPath;
  }

  getServerConfigPath(): string {
    return this.serverConfigPath;
  }

  listAvailableConfigs(): string[] {
    if (!existsSync(this.simulationsPath)) {
      return [];
    }

    return readdirSync(this.simulationsPath)
      .filter((file) => file.endsWith('.json'))
      .map((file) => file.replace('.json', ''));
  }

  saveSimulationConfig(config: SimulationConfig): string {
    mkdirSync(this.simulationsPath, { recursive: true });

    const configPath = join(this.simulationsPath, `${config.name}.json`);
    writeFileSync(configPath, JSON.stringify(config, null, 2));

    return configPath;
  }

  saveMetricsConfig(simulationName: string, metrics: unknown[]): string {
    mkdirSync(this.metricsPath, { recursive: true });

    const metricsPath = join(this.metricsPath, `${simulationName}.json`);
    writeFileSync(metricsPath, JSON.stringify(metrics, null, 2));

    return metricsPath;
  }

  loadSimulationConfig(configName: string): SimulationConfig | null {
    const configPath = join(this.simulationsPath, `${configName}.json`);

    if (!existsSync(configPath)) {
      return null;
    }

    const content = readFileSync(configPath, 'utf-8');
    return JSON.parse(content) as SimulationConfig;
  }

  deleteSimulation(simulationName: string): {
    deleted_files: string[];
    errors: string[];
  } {
    const deletedFiles: string[] = [];
    const errors: string[] = [];

    const extensions = ['.json', '.toml'];
    for (const ext of extensions) {
      const configFile = join(this.simulationsPath, `${simulationName}${ext}`);
      if (existsSync(configFile)) {
        try {
          unlinkSync(configFile);
          deletedFiles.push(configFile);
        } catch (error) {
          errors.push(
            `Failed to delete config ${configFile}: ${error instanceof Error ? error.message : String(error)}`
          );
        }
      }
    }

    const metricsFile = join(this.metricsPath, `${simulationName}.json`);
    if (existsSync(metricsFile)) {
      try {
        unlinkSync(metricsFile);
        deletedFiles.push(metricsFile);
      } catch (error) {
        errors.push(
          `Failed to delete metrics ${metricsFile}: ${error instanceof Error ? error.message : String(error)}`
        );
      }
    }

    return { deleted_files: deletedFiles, errors };
  }

  getDefaultMetricsPath(): string {
    const defaultMetrics = join(this.metricsPath, 'default.json');

    if (existsSync(defaultMetrics)) {
      return defaultMetrics;
    }

    if (existsSync(this.metricsPath)) {
      const metricsFiles = readdirSync(this.metricsPath).filter((f) => f.endsWith('.json'));
      if (metricsFiles.length > 0) {
        return join(this.metricsPath, metricsFiles[0]);
      }
    }

    return '/tmp/empty_metrics.json';
  }
}
