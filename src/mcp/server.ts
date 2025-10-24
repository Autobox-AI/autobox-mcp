import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} from '@modelcontextprotocol/sdk/types.js';
import { join } from 'path';
import { DockerManager } from '../docker/index.js';
import { ConfigManager } from '../config/index.js';
import { SimulationConfig, SimulationConfigSchema, type SimulationStatus } from '../types/index.js';
import { logger } from '../utils/logger.js';
import { tools } from './tools.js';
import { generateMetricsWithLLM } from './metricsGenerator.js';

export class AutoboxMCPServer {
  private server: Server;
  private dockerManager: DockerManager;
  private configManager: ConfigManager;
  private simulations: Map<string, SimulationStatus>;

  constructor() {
    this.server = new Server(
      {
        name: 'autobox-mcp-ts',
        version: '0.1.0',
      },
      {
        capabilities: {
          tools: {},
        },
      }
    );

    this.dockerManager = new DockerManager();
    this.configManager = new ConfigManager();
    this.simulations = new Map();

    this.setupHandlers();
  }

  private setupHandlers(): void {
    this.server.setRequestHandler(ListToolsRequestSchema, async () => ({
      tools,
    }));

    this.server.setRequestHandler(CallToolRequestSchema, async (request) => {
      const { name, arguments: args } = request.params;

      try {
        let result: unknown;

        switch (name) {
          case 'list_simulations':
            result = await this.listSimulations();
            break;
          case 'start_simulation':
            result = args ? await this.startSimulation(args) : { error: 'Missing arguments' };
            break;
          case 'stop_simulation':
            result = args
              ? await this.stopSimulation(args.simulation_id as string)
              : { error: 'Missing arguments' };
            break;
          case 'get_simulation_status':
            result = args
              ? await this.getSimulationStatus(args.simulation_id as string)
              : { error: 'Missing arguments' };
            break;
          case 'get_simulation_logs':
            result = args
              ? await this.getSimulationLogs(
                  args.simulation_id as string,
                  (args.tail as number) || 100
                )
              : { error: 'Missing arguments' };
            break;
          case 'list_available_configs':
            result = await this.listAvailableConfigs();
            break;
          case 'get_simulation_metrics':
            result = args
              ? await this.getSimulationMetrics(
                  args.simulation_id as string,
                  (args.include_docker_stats as boolean) ?? true
                )
              : { error: 'Missing arguments' };
            break;
          case 'create_simulation_config':
            result = args
              ? await this.createSimulationConfig(args)
              : { error: 'Missing arguments' };
            break;
          case 'stop_all_simulations':
            result = await this.stopAllSimulations();
            break;
          case 'create_simulation_metrics':
            result = args
              ? await this.createSimulationMetrics(args)
              : { error: 'Missing arguments' };
            break;
          case 'instruct_agent':
            result = args
              ? await this.instructAgent(
                  args.simulation_id as string,
                  args.agent_name as string,
                  args.instruction as string
                )
              : { error: 'Missing arguments' };
            break;
          case 'delete_simulation':
            result = args
              ? await this.deleteSimulation(args.simulation_name as string)
              : { error: 'Missing arguments' };
            break;
          case 'ping_simulation':
            result = args
              ? await this.pingSimulation(args.simulation_id as string)
              : { error: 'Missing arguments' };
            break;
          case 'get_simulation_health':
            result = args
              ? await this.getSimulationHealth(args.simulation_id as string)
              : { error: 'Missing arguments' };
            break;
          case 'get_simulation_execution_status':
            result = args
              ? await this.getSimulationExecutionStatus(args.simulation_id as string)
              : { error: 'Missing arguments' };
            break;
          case 'abort_simulation':
            result = args
              ? await this.abortSimulation(args.simulation_id as string)
              : { error: 'Missing arguments' };
            break;
          case 'get_simulation_info':
            result = args
              ? await this.getSimulationInfo(args.simulation_id as string)
              : { error: 'Missing arguments' };
            break;
          case 'get_simulation_api_spec':
            result = args
              ? await this.getSimulationApiSpec(args.simulation_id as string)
              : { error: 'Missing arguments' };
            break;
          default:
            result = { error: `Unknown tool: ${name}` };
        }

        return {
          content: [
            {
              type: 'text',
              text: JSON.stringify(result, null, 2),
            },
          ],
        };
      } catch (error) {
        logger.error(`Error in tool ${name}:`, error);
        return {
          content: [
            {
              type: 'text',
              text: JSON.stringify(
                {
                  error: error instanceof Error ? error.message : String(error),
                },
                null,
                2
              ),
            },
          ],
          isError: true,
        };
      }
    });
  }

  private async listSimulations(): Promise<unknown> {
    const running = await this.dockerManager.listRunningSimulations();
    return {
      running,
      tracked: Array.from(this.simulations.keys()),
      total: running.length + this.simulations.size,
    };
  }

  private async startSimulation(args: Record<string, unknown>): Promise<unknown> {
    const { config_name, custom_config, daemon = false } = args;

    let configPath: string;
    let metricsPath: string;

    if (custom_config) {
      const config = custom_config as SimulationConfig;
      configPath = this.configManager.saveSimulationConfig(config);
      metricsPath = this.configManager.getDefaultMetricsPath();
    } else {
      if (!config_name) {
        return { error: 'Either config_name or custom_config must be provided' };
      }

      configPath = join(
        this.configManager.getSimulationsPath(),
        `${config_name as string}.json`
      );
      metricsPath = join(this.configManager.getMetricsPath(), `${config_name as string}.json`);
    }

    const { containerId, hostPort } = await this.dockerManager.startSimulation({
      configPath,
      metricsPath,
      serverConfigPath: this.configManager.getServerConfigPath(),
      daemon: daemon as boolean,
    });

    const simStatus: SimulationStatus = {
      id: containerId,
      name: (custom_config as SimulationConfig)?.name || (config_name as string),
      status: 'running',
      configPath,
    };

    this.simulations.set(containerId, simStatus);

    return {
      simulation_id: containerId,
      status: 'started',
      config: configPath,
      daemon: daemon as boolean,
      api_url: `http://localhost:${hostPort}`,
      host_port: hostPort,
    };
  }

  private async stopSimulation(simulationId: string): Promise<unknown> {
    const success = await this.dockerManager.stopSimulation(simulationId);

    if (success) {
      const sim = this.simulations.get(simulationId);
      if (sim) {
        sim.status = 'stopped';
        this.simulations.set(simulationId, sim);
      }
      return { simulation_id: simulationId, status: 'stopped' };
    }

    return { error: `Failed to stop simulation ${simulationId}` };
  }

  private async stopAllSimulations(): Promise<unknown> {
    const result = await this.dockerManager.stopAllSimulations();

    for (const stopped of result.stopped) {
      const sim = this.simulations.get(stopped.id);
      if (sim) {
        sim.status = 'stopped';
        this.simulations.set(stopped.id, sim);
      }
    }

    return result;
  }

  private async getSimulationStatus(simulationId: string): Promise<unknown> {
    const containerStatus = await this.dockerManager.getContainerStatus(simulationId);

    const sim = this.simulations.get(simulationId);
    if (sim && containerStatus) {
      return {
        id: simulationId,
        name: sim.name,
        status: containerStatus.status,
        container: containerStatus,
      };
    } else if (containerStatus) {
      return {
        id: simulationId,
        status: containerStatus.status,
        container: containerStatus,
      };
    }

    return { error: `Simulation ${simulationId} not found` };
  }

  private async getSimulationLogs(simulationId: string, tail: number): Promise<string> {
    const logs = await this.dockerManager.getLogs(simulationId, tail);
    return logs || `No logs found for simulation ${simulationId}`;
  }

  private async getSimulationMetrics(
    simulationId: string,
    includeDockerStats: boolean
  ): Promise<unknown> {
    const metrics = await this.dockerManager.getSimulationApiMetrics(
      simulationId,
      includeDockerStats
    );

    if (!metrics) {
      return { error: `No metrics available for simulation ${simulationId}` };
    }

    return metrics;
  }

  private async listAvailableConfigs(): Promise<string[]> {
    return this.configManager.listAvailableConfigs();
  }

  private async createSimulationConfig(args: Record<string, unknown>): Promise<unknown> {
    const { name, description, timeout_seconds = 300, agents = [] } = args;

    if (!name || !description) {
      return { error: 'name and description are required' };
    }

    const config: SimulationConfig = {
      name: name as string,
      description: description as string,
      task: description as string,
      timeout_seconds: timeout_seconds as number,
      shutdown_grace_period_seconds: 5,
      evaluator: {
        name: 'EVALUATOR',
        llm: { model: 'gpt-4o-mini' },
        context: '',
      },
      reporter: {
        name: 'REPORTER',
        llm: { model: 'gpt-4o-mini' },
        context: '',
      },
      planner: {
        name: 'PLANNER',
        llm: { model: 'gpt-4o-mini' },
        context: '',
      },
      orchestrator: {
        name: 'ORCHESTRATOR',
        llm: { model: 'gpt-4o-mini' },
        context: '',
      },
      workers: (agents as Array<{ name: string; role?: string; backstory?: string }>).map(
        (agent) => ({
          name: agent.name,
          description: `This is ${agent.name.toLowerCase()} agent`,
          role: agent.role,
          context: agent.backstory || '',
          llm: { model: 'gpt-4o-mini' },
        })
      ),
      logging: {
        verbose: false,
        log_path: 'logs',
        log_file: `${(name as string).toLowerCase().replace(/\s+/g, '_')}.log`,
      },
    };

    const validated = SimulationConfigSchema.parse(config);
    const configPath = this.configManager.saveSimulationConfig(validated);

    return {
      config: validated,
      config_path: configPath,
      message: `Configuration created and saved to ${configPath}. You can now use 'start_simulation' with config_name: '${name}'`,
    };
  }

  private async createSimulationMetrics(args: Record<string, unknown>): Promise<unknown> {
    const { simulation_name, use_llm = true, custom_metrics } = args;

    if (!simulation_name) {
      return { error: 'simulation_name is required' };
    }

    const simConfig = this.configManager.loadSimulationConfig(simulation_name as string);
    if (!simConfig) {
      return { error: `Simulation config '${simulation_name}' not found` };
    }

    let metrics: unknown[];

    if (use_llm) {
      const generated = await generateMetricsWithLLM(simConfig);
      if (!generated) {
        return { error: 'Failed to generate metrics with LLM' };
      }
      metrics = generated;
    } else {
      if (!custom_metrics || !Array.isArray(custom_metrics)) {
        return { error: 'No custom metrics provided and use_llm is false' };
      }
      metrics = custom_metrics;
    }

    const metricsPath = this.configManager.saveMetricsConfig(simulation_name as string, metrics);

    return {
      metrics,
      metrics_path: metricsPath,
      message: `Metrics created and saved to ${metricsPath}`,
      simulation_name,
    };
  }

  private async instructAgent(
    simulationId: string,
    agentName: string,
    instruction: string
  ): Promise<unknown> {
    return await this.dockerManager.instructAgent(simulationId, agentName, instruction);
  }

  private async deleteSimulation(simulationName: string): Promise<unknown> {
    const result = this.configManager.deleteSimulation(simulationName);

    const runningSim = Array.from(this.simulations.entries()).find(
      ([_id, status]) => status.name === simulationName && status.status === 'running'
    );

    const response: Record<string, unknown> = {
      simulation_name: simulationName,
      deleted_files: result.deleted_files,
      success: result.deleted_files.length > 0,
    };

    if (result.errors.length > 0) {
      response.errors = result.errors;
    }

    if (runningSim) {
      response.warning = `Simulation '${simulationName}' is currently running with ID ${runningSim[0]}. Configuration deleted but container still active.`;
    }

    if (result.deleted_files.length === 0 && result.errors.length === 0) {
      response.message = `No files found for simulation '${simulationName}'`;
    } else if (result.deleted_files.length > 0) {
      response.message = `Successfully deleted ${result.deleted_files.length} file(s) for simulation '${simulationName}'`;
    }

    return response;
  }


  private async pingSimulation(simulationId: string): Promise<unknown> {
    return await this.dockerManager.pingSimulation(simulationId);
  }

  private async getSimulationHealth(simulationId: string): Promise<unknown> {
    return await this.dockerManager.getSimulationHealth(simulationId);
  }

  private async getSimulationExecutionStatus(simulationId: string): Promise<unknown> {
    return await this.dockerManager.getSimulationExecutionStatus(simulationId);
  }

  private async abortSimulation(simulationId: string): Promise<unknown> {
    return await this.dockerManager.abortSimulation(simulationId);
  }

  private async getSimulationInfo(simulationId: string): Promise<unknown> {
    return await this.dockerManager.getSimulationInfo(simulationId);
  }

  private async getSimulationApiSpec(simulationId: string): Promise<unknown> {
    return await this.dockerManager.getSimulationApiSpec(simulationId);
  }

  async run(): Promise<void> {
    const transport = new StdioServerTransport();
    await this.server.connect(transport);
    logger.info('Autobox MCP server running');
  }
}
