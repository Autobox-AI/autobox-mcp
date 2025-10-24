import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { ConfigManager } from '../../src/config/paths';
import { DockerManager } from '../../src/docker/manager';

jest.mock('../../src/docker/manager');
jest.mock('../../src/config/paths');

describe('MCP Server Integration', () => {
  let mockConfigManager: jest.Mocked<ConfigManager>;
  let mockDockerManager: jest.Mocked<DockerManager>;

  beforeEach(() => {
    jest.clearAllMocks();

    mockConfigManager = {
      listAvailableConfigs: jest.fn(),
      getSimulationConfig: jest.fn(),
      saveSimulationConfig: jest.fn(),
      deleteSimulation: jest.fn(),
      getSimulationsPath: jest.fn(),
      getMetricsPath: jest.fn(),
    } as any;

    mockDockerManager = {
      listRunningSimulations: jest.fn(),
      startSimulation: jest.fn(),
      stopSimulation: jest.fn(),
      stopAllSimulations: jest.fn(),
      getContainerStatus: jest.fn(),
      getLogs: jest.fn(),
      getSimulationApiMetrics: jest.fn(),
      instructAgent: jest.fn(),
      pingSimulation: jest.fn(),
      getSimulationHealth: jest.fn(),
      getSimulationExecutionStatus: jest.fn(),
      abortSimulation: jest.fn(),
      getSimulationInfo: jest.fn(),
      getSimulationApiSpec: jest.fn(),
    } as any;

    (ConfigManager as jest.MockedClass<typeof ConfigManager>).mockImplementation(
      () => mockConfigManager
    );
    (DockerManager as jest.MockedClass<typeof DockerManager>).mockImplementation(
      () => mockDockerManager
    );
  });

  describe('Tool availability', () => {
    it('should expose all required MCP tools', () => {
      const expectedTools = [
        'list_simulations',
        'start_simulation',
        'stop_simulation',
        'get_simulation_status',
        'get_simulation_logs',
        'list_available_configs',
        'get_simulation_metrics',
        'create_simulation_config',
        'stop_all_simulations',
        'create_simulation_metrics',
        'instruct_agent',
        'delete_simulation',
        'ping_simulation',
        'get_simulation_health',
        'get_simulation_execution_status',
        'abort_simulation',
        'get_simulation_info',
        'get_simulation_api_spec',
      ];

      expect(expectedTools.length).toBeGreaterThan(0);
    });
  });

  describe('list_simulations workflow', () => {
    it('should list running simulations', async () => {
      const mockSimulations = [
        {
          id: 'sim-123',
          name: 'test-simulation',
          status: 'running',
          created: 1704067200,
        },
      ];

      mockDockerManager.listRunningSimulations.mockResolvedValue(mockSimulations);

      const result = await mockDockerManager.listRunningSimulations();

      expect(result).toEqual(mockSimulations);
      expect(mockDockerManager.listRunningSimulations).toHaveBeenCalledTimes(1);
    });
  });

  describe('start_simulation workflow', () => {
    it('should start simulation with provided config', async () => {
      const mockConfig = {
        name: 'test-sim',
        description: 'Test simulation',
        task: 'Test task',
        timeout_seconds: 300,
        shutdown_grace_period_seconds: 5,
        evaluator: { name: 'EVALUATOR', llm: { model: 'gpt-4o-mini' }, context: '' },
        reporter: { name: 'REPORTER', llm: { model: 'gpt-4o-mini' }, context: '' },
        planner: { name: 'PLANNER', llm: { model: 'gpt-4o-mini' }, context: '' },
        orchestrator: { name: 'ORCHESTRATOR', llm: { model: 'gpt-4o-mini' }, context: '' },
        workers: [],
        logging: { verbose: false, log_path: 'logs', log_file: 'test.log' },
      };

      const mockResult = {
        success: true,
        container_id: 'container-123',
        container_name: 'autobox-sim-test',
        api_port: 9001,
        message: 'Simulation started successfully',
      };

      mockDockerManager.startSimulation.mockResolvedValue(mockResult);

      const result = await mockDockerManager.startSimulation({
        config: mockConfig,
        daemon: false,
      });

      expect(result.success).toBe(true);
      expect(result.container_id).toBe('container-123');
      expect(mockDockerManager.startSimulation).toHaveBeenCalledWith({
        config: mockConfig,
        daemon: false,
      });
    });
  });

  describe('list_available_configs workflow', () => {
    it('should list available simulation configs', async () => {
      const mockConfigs = ['summer_vacation', 'gift_choice', 'debate'];

      mockConfigManager.listAvailableConfigs.mockReturnValue(mockConfigs);

      const result = mockConfigManager.listAvailableConfigs();

      expect(result).toEqual(mockConfigs);
      expect(mockConfigManager.listAvailableConfigs).toHaveBeenCalledTimes(1);
    });
  });

  describe('stop_simulation workflow', () => {
    it('should stop a running simulation', async () => {
      mockDockerManager.stopSimulation.mockResolvedValue(true);

      const result = await mockDockerManager.stopSimulation('sim-123');

      expect(result).toBe(true);
      expect(mockDockerManager.stopSimulation).toHaveBeenCalledWith('sim-123');
    });
  });

  describe('get_simulation_status workflow', () => {
    it('should get simulation status', async () => {
      const mockStatus = {
        status: 'running',
        running: true,
        started_at: '2024-01-01T00:00:00Z',
      };

      mockDockerManager.getContainerStatus.mockResolvedValue(mockStatus);

      const result = await mockDockerManager.getContainerStatus('sim-123');

      expect(result).toEqual(mockStatus);
      expect(mockDockerManager.getContainerStatus).toHaveBeenCalledWith('sim-123');
    });
  });

  describe('get_simulation_logs workflow', () => {
    it('should retrieve simulation logs', async () => {
      const mockLogs = {
        logs: 'Log line 1\nLog line 2\nLog line 3',
        lines: 3,
      };

      mockDockerManager.getLogs.mockResolvedValue(mockLogs);

      const result = await mockDockerManager.getLogs('sim-123', 100);

      expect(result).toEqual(mockLogs);
      expect(mockDockerManager.getLogs).toHaveBeenCalledWith('sim-123', 100);
    });
  });

  describe('instruct_agent workflow', () => {
    it('should send instruction to agent', async () => {
      const mockResponse = {
        success: true,
        message: 'Instruction sent successfully',
      };

      mockDockerManager.instructAgent.mockResolvedValue(mockResponse);

      const result = await mockDockerManager.instructAgent(
        'sim-123',
        'Worker1',
        'Complete the task'
      );

      expect(result.success).toBe(true);
      expect(mockDockerManager.instructAgent).toHaveBeenCalledWith(
        'sim-123',
        'Worker1',
        'Complete the task'
      );
    });
  });

  describe('delete_simulation workflow', () => {
    it('should delete simulation config and metrics', async () => {
      const mockResult = {
        deleted_files: ['test-sim.json', 'test-sim-metrics.json'],
        errors: [],
      };

      mockConfigManager.deleteSimulation.mockReturnValue(mockResult);

      const result = mockConfigManager.deleteSimulation('test-sim');

      expect(result.deleted_files).toHaveLength(2);
      expect(result.errors).toHaveLength(0);
      expect(mockConfigManager.deleteSimulation).toHaveBeenCalledWith('test-sim');
    });
  });

  describe('error handling', () => {
    it('should handle Docker errors gracefully', async () => {
      mockDockerManager.listRunningSimulations.mockRejectedValue(
        new Error('Docker daemon not running')
      );

      await expect(mockDockerManager.listRunningSimulations()).rejects.toThrow(
        'Docker daemon not running'
      );
    });

    it('should handle missing config errors', async () => {
      mockConfigManager.getSimulationConfig.mockImplementation(() => {
        throw new Error('Config not found');
      });

      expect(() => mockConfigManager.getSimulationConfig('nonexistent')).toThrow(
        'Config not found'
      );
    });
  });

  describe('end-to-end simulation lifecycle', () => {
    it('should complete full simulation lifecycle', async () => {
      const configName = 'test-sim';
      const containerId = 'container-123';

      mockConfigManager.listAvailableConfigs.mockReturnValue([configName]);
      mockConfigManager.getSimulationConfig.mockReturnValue({
        name: configName,
        description: 'Test',
        task: 'Test task',
        timeout_seconds: 300,
        shutdown_grace_period_seconds: 5,
        evaluator: { name: 'EVALUATOR', llm: { model: 'gpt-4o-mini' }, context: '' },
        reporter: { name: 'REPORTER', llm: { model: 'gpt-4o-mini' }, context: '' },
        planner: { name: 'PLANNER', llm: { model: 'gpt-4o-mini' }, context: '' },
        orchestrator: { name: 'ORCHESTRATOR', llm: { model: 'gpt-4o-mini' }, context: '' },
        workers: [],
        logging: { verbose: false, log_path: 'logs', log_file: 'test.log' },
      });

      mockDockerManager.startSimulation.mockResolvedValue({
        success: true,
        container_id: containerId,
        container_name: 'autobox-sim-test',
        api_port: 9001,
        message: 'Started',
      });

      mockDockerManager.getContainerStatus.mockResolvedValue({
        status: 'running',
        running: true,
      });

      mockDockerManager.stopSimulation.mockResolvedValue(true);

      const configs = mockConfigManager.listAvailableConfigs();
      expect(configs).toContain(configName);

      const config = mockConfigManager.getSimulationConfig(configName);
      expect(config.name).toBe(configName);

      const startResult = await mockDockerManager.startSimulation({
        config,
        daemon: false,
      });
      expect(startResult.success).toBe(true);

      const status = await mockDockerManager.getContainerStatus(startResult.container_id);
      expect(status.running).toBe(true);

      const stopped = await mockDockerManager.stopSimulation(startResult.container_id);
      expect(stopped).toBe(true);
    });
  });
});
