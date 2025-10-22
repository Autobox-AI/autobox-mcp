import Docker from 'dockerode';
import { homedir, platform } from 'os';
import { join } from 'path';
import type { ContainerStats, SimulationMetrics, SimulationStatus } from '../types/index.js';
import { logger } from '../utils/logger.js';

interface StartSimulationOptions {
  configPath: string;
  metricsPath: string;
  serverConfigPath?: string;
  daemon?: boolean; // Optional: run in daemon mode (default: false)
}

export class DockerManager {
  private client: Docker;
  private imageName = 'autobox-engine:latest';

  constructor() {
    try {
      this.client = new Docker();
    } catch (error) {
      logger.error('Failed to initialize Docker client:', error);
      throw error;
    }
  }

  async listRunningSimulations(): Promise<SimulationStatus[]> {
    try {
      const containers = await this.client.listContainers({
        filters: { label: ['com.autobox.simulation=true'] },
      });

      return containers.map((container) => ({
        id: container.Id.substring(0, 12),
        name: container.Names[0]?.replace(/^\//, '') || container.Id.substring(0, 12),
        status: container.State,
        created: new Date(container.Created * 1000).toISOString(),
        running: container.State === 'running',
      }));
    } catch (error) {
      logger.error('Error listing containers:', error);
      return [];
    }
  }

  async startSimulation(options: StartSimulationOptions): Promise<{ containerId: string; hostPort: number }> {
    const { configPath, daemon = false } = options;
    const configName = configPath.split('/').pop()?.replace('.json', '') || 'unknown';

        const apiPort = 9000;
    const hostPort = await this.findAvailablePort();

    logger.info(`Starting simulation ${configName} on host port ${hostPort}`);

    const homeDir = homedir();
    const autoboxPath = join(homeDir, '.autobox');
    const runningInDocker = process.env.HOST_HOME !== undefined;

    const hostAutoboxPath = runningInDocker
      ? this.resolveHostPath(process.env.HOST_HOME || homeDir)
      : autoboxPath;

    const volumes = {
      [`${hostAutoboxPath}/config`]: {
        bind: '/app/configs',
        mode: 'ro',
      },
    };

    const containerName = `autobox-sim-${Date.now()}`;

    const container = await this.client.createContainer({
      Image: this.imageName,
      name: containerName,
      ExposedPorts: {
        [`${apiPort}/tcp`]: {},
      },
      Cmd: [
        '--config',
        '/app/configs',
        '--simulation-name',
        configName,
        ...(daemon ? ['--daemon'] : []),
      ],
      Env: [
        `OPENAI_API_KEY=${process.env.OPENAI_API_KEY || ''}`,
        `JWT_SECRET=${process.env.JWT_SECRET || 'dev-secret-key-change-in-production'}`,
        `JWT_EXPIRES_IN=${process.env.JWT_EXPIRES_IN || '24h'}`,
        'OBJC_DISABLE_INITIALIZE_FORK_SAFETY=TRUE',
        'PYTHONUNBUFFERED=1',
        `AUTOBOX_EXTERNAL_PORT=${hostPort}`,
      ],
      HostConfig: {
        Binds: Object.entries(volumes).map(([src, { bind, mode }]) => `${src}:${bind}:${mode}`),
        PortBindings: {
          [`${apiPort}/tcp`]: [{ HostPort: hostPort.toString() }],
        },
        AutoRemove: false,
      },
      Labels: {
        'com.autobox.simulation': 'true',
        'com.autobox.name': configName,
        'com.autobox.config_path': configPath,
        'com.autobox.created_at': Date.now().toString(),
        'autobox.api_port': apiPort.toString(),
      },
    });

    await container.start();
    logger.info(`Started simulation container: ${container.id.substring(0, 12)}`);
    logger.info(`🌐 Access simulation API at: http://localhost:${hostPort}`);

    return {
      containerId: container.id.substring(0, 12),
      hostPort,
    };
  }

  async stopSimulation(containerId: string): Promise<boolean> {
    try {
      const container = this.client.getContainer(containerId);
      await container.stop({ t: 10 });
      await container.remove();
      logger.info(`Stopped simulation container: ${containerId}`);
      return true;
    } catch (error) {
      if ((error as { statusCode?: number }).statusCode === 404) {
        logger.warn(`Container not found: ${containerId}`);
        return false;
      }
      logger.error('Error stopping container:', error);
      return false;
    }
  }

  async stopAllSimulations(): Promise<{
    stopped: Array<{ id: string; name: string }>;
    failed: Array<{ id: string; name: string; error: string }>;
    total_stopped: number;
    total_failed: number;
  }> {
    const stopped: Array<{ id: string; name: string }> = [];
    const failed: Array<{ id: string; name: string; error: string }> = [];

    try {
      const containers = await this.client.listContainers({
        filters: {
          label: ['com.autobox.simulation=true'],
          status: ['running'],
        },
      });

      await Promise.all(
        containers.map(async (containerInfo) => {
          const containerId = containerInfo.Id.substring(0, 12);
          const containerName =
            containerInfo.Names[0]?.replace(/^\//, '') || containerInfo.Id.substring(0, 12);

          try {
            const container = this.client.getContainer(containerInfo.Id);
            await container.stop({ t: 10 });
            await container.remove();
            stopped.push({ id: containerId, name: containerName });
            logger.info(`Stopped simulation container: ${containerName}`);
          } catch (error) {
            const errorMessage = error instanceof Error ? error.message : String(error);
            failed.push({ id: containerId, name: containerName, error: errorMessage });
            logger.error(`Failed to stop container ${containerName}:`, error);
          }
        })
      );

      return {
        stopped,
        failed,
        total_stopped: stopped.length,
        total_failed: failed.length,
      };
    } catch (error) {
      logger.error('Error listing/stopping containers:', error);
      return { stopped, failed, total_stopped: 0, total_failed: 0 };
    }
  }

  async getContainerStatus(
    containerId: string
  ): Promise<{ id: string; name: string; status: string; running: boolean; ports?: Record<string, string> } | null> {
    try {
      const container = this.client.getContainer(containerId);
      const info = await container.inspect();

      // Extract port mappings
      const ports: Record<string, string> = {};
      if (info.NetworkSettings?.Ports) {
        for (const [containerPort, hostBindings] of Object.entries(info.NetworkSettings.Ports)) {
          if (hostBindings && Array.isArray(hostBindings) && hostBindings.length > 0) {
            const hostPort = hostBindings[0].HostPort;
            ports[containerPort] = `localhost:${hostPort}`;
          }
        }
      }

      return {
        id: info.Id.substring(0, 12),
        name: info.Name.replace(/^\//, ''),
        status: info.State.Status,
        running: info.State.Running,
        ports: Object.keys(ports).length > 0 ? ports : undefined,
      };
    } catch (error) {
      if ((error as { statusCode?: number }).statusCode === 404) {
        return null;
      }
      logger.error('Error getting container status:', error);
      return null;
    }
  }

  async getLogs(containerId: string, tail = 100): Promise<string | null> {
    try {
      const container = this.client.getContainer(containerId);
      const logStream = await container.logs({
        stdout: true,
        stderr: true,
        tail,
        timestamps: true,
        follow: false,
      });

      // Docker logs return a Buffer, but it's multiplexed with 8-byte headers
      // We need to properly demux it or convert it carefully
      if (Buffer.isBuffer(logStream)) {
        // Simple approach: strip the headers (first 8 bytes of each frame)
        const lines: string[] = [];
        let offset = 0;
        const buffer = logStream as Buffer;

        while (offset < buffer.length) {
          // Docker frame format: [stream_type, 0, 0, 0, size1, size2, size3, size4, ...data]
          if (offset + 8 > buffer.length) break;

          const size = buffer.readUInt32BE(offset + 4);
          const frameStart = offset + 8;
          const frameEnd = frameStart + size;

          if (frameEnd > buffer.length) break;

          const line = buffer.toString('utf-8', frameStart, frameEnd);
          lines.push(line);
          offset = frameEnd;
        }

        return lines.join('');
      }

      // Fallback for non-buffer responses
      return String(logStream);
    } catch (error) {
      if ((error as { statusCode?: number }).statusCode === 404) {
        return null;
      }
      logger.error('Error getting logs:', error);
      throw error; // Re-throw to see the actual error
    }
  }

  async getContainerStats(containerId: string): Promise<ContainerStats | null> {
    try {
      const container = this.client.getContainer(containerId);
      const stats = await container.stats({ stream: false });

      const cpuDelta =
        stats.cpu_stats.cpu_usage.total_usage - stats.precpu_stats.cpu_usage.total_usage;
      const systemDelta = stats.cpu_stats.system_cpu_usage - stats.precpu_stats.system_cpu_usage;
      const cpuPercent = systemDelta > 0 && cpuDelta > 0 ? (cpuDelta / systemDelta) * 100 : 0;

      const memoryUsage = stats.memory_stats.usage || 0;
      const memoryLimit = stats.memory_stats.limit || 0;
      const memoryPercent = memoryLimit > 0 ? (memoryUsage / memoryLimit) * 100 : 0;

      let networkRx = 0;
      let networkTx = 0;
      if (stats.networks) {
        Object.values(stats.networks).forEach((network: any) => {
          networkRx += network.rx_bytes || 0;
          networkTx += network.tx_bytes || 0;
        });
      }

      return {
        cpu_percent: Math.round(cpuPercent * 100) / 100,
        memory_usage_mb: Math.round((memoryUsage / 1024 / 1024) * 100) / 100,
        memory_limit_mb: Math.round((memoryLimit / 1024 / 1024) * 100) / 100,
        memory_percent: Math.round(memoryPercent * 100) / 100,
        network_rx_mb: Math.round((networkRx / 1024 / 1024) * 100) / 100,
        network_tx_mb: Math.round((networkTx / 1024 / 1024) * 100) / 100,
      };
    } catch (error) {
      if ((error as { statusCode?: number }).statusCode === 404) {
        return null;
      }
      logger.error('Error getting container stats:', error);
      return null;
    }
  }

  async getSimulationApiMetrics(
    containerId: string,
    includeDockerStats = true
  ): Promise<SimulationMetrics | null> {
    try {
      const container = this.client.getContainer(containerId);
      const info = await container.inspect();

      if (!info.State.Running) {
        return null;
      }

      const apiPort = info.Config.Labels?.['autobox.api_port'] || '9000';
      const portBindings = info.NetworkSettings.Ports?.[`${apiPort}/tcp`];

      let metrics: SimulationMetrics | null = null;

      if (portBindings && portBindings.length > 0) {
        const hostPort = portBindings[0].HostPort;
        const hostIp = portBindings[0].HostIp === '0.0.0.0' ? 'localhost' : portBindings[0].HostIp;

        metrics = await this.fetchMetricsFromApi(`http://${hostIp}:${hostPort}/v1/metrics`);
      }

      if (!metrics) {
        const networks = info.NetworkSettings.Networks || {};
        for (const network of Object.values(networks)) {
          if (network.IPAddress) {
            metrics = await this.fetchMetricsFromApi(
              `http://${network.IPAddress}:${apiPort}/v1/metrics`
            );
            if (metrics) break;
          }
        }
      }

      if (!metrics) {
        return null;
      }

      metrics.simulation_id = containerId;
      metrics.timestamp = Date.now();

      if (includeDockerStats) {
        const dockerStats = await this.getContainerStats(containerId);
        if (dockerStats) {
          metrics.docker_stats = dockerStats;
        }
      }

      return metrics;
    } catch (error) {
      logger.error('Error getting API metrics:', error);
      return null;
    }
  }

  async instructAgent(
    containerId: string,
    agentName: string,
    instruction: string
  ): Promise<{ success: boolean; message?: string; error?: string }> {
    try {
      const container = this.client.getContainer(containerId);
      const info = await container.inspect();

      if (!info.State.Running) {
        return { success: false, error: `Simulation ${containerId} is not running` };
      }

      const apiPort = info.Config.Labels?.['autobox.api_port'] || '9000';
      const portBindings = info.NetworkSettings.Ports?.[`${apiPort}/tcp`];

      if (portBindings && portBindings.length > 0) {
        const hostPort = portBindings[0].HostPort;
        const hostIp = portBindings[0].HostIp === '0.0.0.0' ? 'localhost' : portBindings[0].HostIp;
        const url = `http://${hostIp}:${hostPort}/v1/instructions/agents/${agentName.toLowerCase()}`;

        return await this.sendInstructionToApi(url, instruction);
      }

      const networks = info.NetworkSettings.Networks || {};
      for (const network of Object.values(networks)) {
        if (network.IPAddress) {
          const url = `http://${network.IPAddress}:${apiPort}/v1/instructions/agents/${agentName.toLowerCase()}`;
          const result = await this.sendInstructionToApi(url, instruction);
          if (result.success) return result;
        }
      }

      return { success: false, error: 'Could not connect to simulation API' };
    } catch (error) {
      logger.error('Error instructing agent:', error);
      return { success: false, error: error instanceof Error ? error.message : String(error) };
    }
  }


  async pingSimulation(containerId: string): Promise<{ success: boolean; message?: string; error?: string }> {
    try {
      const container = this.client.getContainer(containerId);
      const info = await container.inspect();

      if (!info.State.Running) {
        return { success: false, error: `Simulation ${containerId} is not running` };
      }

      const apiPort = info.Config.Labels?.['autobox.api_port'] || '9000';
      const portBindings = info.NetworkSettings.Ports?.[`${apiPort}/tcp`];

      if (portBindings && portBindings.length > 0) {
        const hostPort = portBindings[0].HostPort;
        const hostIp = portBindings[0].HostIp === '0.0.0.0' ? 'localhost' : portBindings[0].HostIp;
        const result = await this.fetchTextFromApi(`http://${hostIp}:${hostPort}/ping`);
        if (result === 'pong') return { success: true, message: 'Simulation API is responsive' };
      }

      const networks = info.NetworkSettings.Networks || {};
      for (const network of Object.values(networks)) {
        if (network.IPAddress) {
          const result = await this.fetchTextFromApi(`http://${network.IPAddress}:${apiPort}/ping`);
          if (result === 'pong') return { success: true, message: 'Simulation API is responsive' };
        }
      }

      return { success: false, error: 'Could not connect to simulation API' };
    } catch (error) {
      logger.error('Error pinging simulation:', error);
      return { success: false, error: error instanceof Error ? error.message : String(error) };
    }
  }

  async getSimulationHealth(containerId: string): Promise<unknown> {
    try {
      const container = this.client.getContainer(containerId);
      const info = await container.inspect();

      if (!info.State.Running) {
        return { error: `Simulation ${containerId} is not running` };
      }

      const apiPort = info.Config.Labels?.['autobox.api_port'] || '9000';
      const portBindings = info.NetworkSettings.Ports?.[`${apiPort}/tcp`];

      if (portBindings && portBindings.length > 0) {
        const hostPort = portBindings[0].HostPort;
        const hostIp = portBindings[0].HostIp === '0.0.0.0' ? 'localhost' : portBindings[0].HostIp;
        const result = await this.fetchFromApi(`http://${hostIp}:${hostPort}/health`);
        if (result) return result;
      }

      const networks = info.NetworkSettings.Networks || {};
      for (const network of Object.values(networks)) {
        if (network.IPAddress) {
          const result = await this.fetchFromApi(`http://${network.IPAddress}:${apiPort}/health`);
          if (result) return result;
        }
      }

      return { error: 'Could not connect to simulation API' };
    } catch (error) {
      logger.error('Error getting simulation health:', error);
      return { error: error instanceof Error ? error.message : String(error) };
    }
  }

  async getSimulationExecutionStatus(containerId: string): Promise<unknown> {
    try {
      const container = this.client.getContainer(containerId);
      const info = await container.inspect();

      if (!info.State.Running) {
        return { error: `Simulation ${containerId} is not running` };
      }

      const apiPort = info.Config.Labels?.['autobox.api_port'] || '9000';
      const portBindings = info.NetworkSettings.Ports?.[`${apiPort}/tcp`];

      if (portBindings && portBindings.length > 0) {
        const hostPort = portBindings[0].HostPort;
        const hostIp = portBindings[0].HostIp === '0.0.0.0' ? 'localhost' : portBindings[0].HostIp;
        const result = await this.fetchFromApi(`http://${hostIp}:${hostPort}/v1/status`);
        if (result) return result;
      }

      const networks = info.NetworkSettings.Networks || {};
      for (const network of Object.values(networks)) {
        if (network.IPAddress) {
          const result = await this.fetchFromApi(`http://${network.IPAddress}:${apiPort}/v1/status`);
          if (result) return result;
        }
      }

      return { error: 'Could not connect to simulation API' };
    } catch (error) {
      logger.error('Error getting simulation execution status:', error);
      return { error: error instanceof Error ? error.message : String(error) };
    }
  }

  async abortSimulation(containerId: string): Promise<{ success: boolean; message?: string; error?: string }> {
    try {
      const container = this.client.getContainer(containerId);
      const info = await container.inspect();

      if (!info.State.Running) {
        return { success: false, error: `Simulation ${containerId} is not running` };
      }

      const apiPort = info.Config.Labels?.['autobox.api_port'] || '9000';
      const portBindings = info.NetworkSettings.Ports?.[`${apiPort}/tcp`];

      if (portBindings && portBindings.length > 0) {
        const hostPort = portBindings[0].HostPort;
        const hostIp = portBindings[0].HostIp === '0.0.0.0' ? 'localhost' : portBindings[0].HostIp;
        const url = `http://${hostIp}:${hostPort}/v1/abort`;
        const result = await this.postToApi(url);
        if (result.success) return result;
      }

      const networks = info.NetworkSettings.Networks || {};
      for (const network of Object.values(networks)) {
        if (network.IPAddress) {
          const url = `http://${network.IPAddress}:${apiPort}/v1/abort`;
          const result = await this.postToApi(url);
          if (result.success) return result;
        }
      }

      return { success: false, error: 'Could not connect to simulation API' };
    } catch (error) {
      logger.error('Error aborting simulation:', error);
      return { success: false, error: error instanceof Error ? error.message : String(error) };
    }
  }

  async getSimulationInfo(containerId: string): Promise<unknown> {
    try {
      const container = this.client.getContainer(containerId);
      const info = await container.inspect();

      if (!info.State.Running) {
        return { error: `Simulation ${containerId} is not running` };
      }

      const apiPort = info.Config.Labels?.['autobox.api_port'] || '9000';
      const portBindings = info.NetworkSettings.Ports?.[`${apiPort}/tcp`];

      if (portBindings && portBindings.length > 0) {
        const hostPort = portBindings[0].HostPort;
        const hostIp = portBindings[0].HostIp === '0.0.0.0' ? 'localhost' : portBindings[0].HostIp;
        const result = await this.fetchFromApi(`http://${hostIp}:${hostPort}/v1/info`);
        if (result) return result;
      }

      const networks = info.NetworkSettings.Networks || {};
      for (const network of Object.values(networks)) {
        if (network.IPAddress) {
          const result = await this.fetchFromApi(`http://${network.IPAddress}:${apiPort}/v1/info`);
          if (result) return result;
        }
      }

      return { error: 'Could not connect to simulation API' };
    } catch (error) {
      logger.error('Error getting simulation info:', error);
      return { error: error instanceof Error ? error.message : String(error) };
    }
  }

  async getSimulationApiSpec(containerId: string): Promise<unknown> {
    try {
      const container = this.client.getContainer(containerId);
      const info = await container.inspect();

      if (!info.State.Running) {
        return { error: `Simulation ${containerId} is not running` };
      }

      const apiPort = info.Config.Labels?.['autobox.api_port'] || '9000';
      const portBindings = info.NetworkSettings.Ports?.[`${apiPort}/tcp`];

      if (portBindings && portBindings.length > 0) {
        const hostPort = portBindings[0].HostPort;
        const hostIp = portBindings[0].HostIp === '0.0.0.0' ? 'localhost' : portBindings[0].HostIp;
        const result = await this.fetchFromApi(`http://${hostIp}:${hostPort}/`);
        if (result) return result;
      }

      const networks = info.NetworkSettings.Networks || {};
      for (const network of Object.values(networks)) {
        if (network.IPAddress) {
          const result = await this.fetchFromApi(`http://${network.IPAddress}:${apiPort}/`);
          if (result) return result;
        }
      }

      return { error: 'Could not connect to simulation API' };
    } catch (error) {
      logger.error('Error getting simulation API spec:', error);
      return { error: error instanceof Error ? error.message : String(error) };
    }
  }

  private async fetchMetricsFromApi(url: string): Promise<SimulationMetrics | null> {
    try {
      const response = await fetch(url, {
        signal: AbortSignal.timeout(5000),
      });

      if (response.ok) {
        return (await response.json()) as SimulationMetrics;
      }
    } catch (error) {
      logger.debug(`Failed to fetch metrics from ${url}:`, error);
    }
    return null;
  }

  private async sendInstructionToApi(
    url: string,
    instruction: string
  ): Promise<{ success: boolean; message?: string; error?: string }> {
    try {
      const response = await fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ instruction }),
        signal: AbortSignal.timeout(10000),
      });

      if (response.ok) {
        return {
          success: true,
          message: 'Instruction sent successfully',
        };
      }

      return {
        success: false,
        error: `API returned status ${response.status}`,
      };
    } catch (error) {
      return {
        success: false,
        error: error instanceof Error ? error.message : String(error),
      };
    }
  }


  private async fetchFromApi(url: string): Promise<unknown | null> {
    try {
      const response = await fetch(url, {
        signal: AbortSignal.timeout(5000),
      });

      if (response.ok) {
        return await response.json();
      }
    } catch (error) {
      logger.debug(`Failed to fetch from ${url}:`, error);
    }
    return null;
  }


  private async fetchTextFromApi(url: string): Promise<string | null> {
    try {
      const response = await fetch(url, {
        signal: AbortSignal.timeout(5000),
      });

      if (response.ok) {
        return await response.text();
      }
    } catch (error) {
      logger.debug(`Failed to fetch text from ${url}:`, error);
    }
    return null;
  }

  private async postToApi(url: string, body?: Record<string, unknown>): Promise<{ success: boolean; message?: string; error?: string }> {
    try {
      const response = await fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: body ? JSON.stringify(body) : undefined,
        signal: AbortSignal.timeout(10000),
      });

      if (response.ok) {
        return {
          success: true,
          message: 'Request completed successfully',
        };
      }

      return {
        success: false,
        error: `API returned status ${response.status}`,
      };
    } catch (error) {
      return {
        success: false,
        error: error instanceof Error ? error.message : String(error),
      };
    }
  }

  private async findAvailablePort(): Promise<number> {
    const net = await import('net');
    return new Promise((resolve, reject) => {
      const server = net.createServer();
      server.unref();
      server.on('error', reject);
      server.listen(0, () => {
        const address = server.address();
        if (address && typeof address !== 'string') {
          const port = address.port;
          server.close(() => resolve(port));
        } else {
          reject(new Error('Failed to get port'));
        }
      });
    });
  }

  private resolveHostPath(hostHome: string): string {
    const username = process.env.HOST_USER || 'root';

    if (platform() === 'darwin' || hostHome.includes('/Users')) {
      return `/Users/${username}/.autobox`;
    }

    return `/home/${username}/.autobox`;
  }
}
