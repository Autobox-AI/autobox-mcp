import { DockerManager } from '../../src/docker/manager';

jest.mock('dockerode');
jest.mock('../../src/utils/logger');

describe('DockerManager', () => {
  let dockerManager: DockerManager;

  beforeEach(() => {
    jest.clearAllMocks();
    dockerManager = new DockerManager();
  });

  describe('listRunningSimulations', () => {
    it('should list running simulations', async () => {
      const mockContainers = [
        {
          Id: 'abc123def456',
          Names: ['/autobox-sim-123'],
          State: 'running',
          Created: 1704067200,
        },
      ];

      (dockerManager as any).client.listContainers = jest
        .fn()
        .mockResolvedValue(mockContainers);

      const result = await dockerManager.listRunningSimulations();

      expect(result).toHaveLength(1);
      expect(result[0].id).toBe('abc123def456');
      expect(result[0].name).toBe('autobox-sim-123');
      expect(result[0].status).toBe('running');
    });

    it('should return empty array on error', async () => {
      (dockerManager as any).client.listContainers = jest
        .fn()
        .mockRejectedValue(new Error('Docker error'));

      const result = await dockerManager.listRunningSimulations();

      expect(result).toEqual([]);
    });
  });

  describe('stopSimulation', () => {
    it('should stop and remove container successfully', async () => {
      const mockContainer = {
        stop: jest.fn().mockResolvedValue(undefined),
        remove: jest.fn().mockResolvedValue(undefined),
      };

      (dockerManager as any).client.getContainer = jest.fn().mockReturnValue(mockContainer);

      const result = await dockerManager.stopSimulation('abc123');

      expect(result).toBe(true);
      expect(mockContainer.stop).toHaveBeenCalledWith({ t: 10 });
      expect(mockContainer.remove).toHaveBeenCalled();
    });

    it('should return false when container not found', async () => {
      (dockerManager as any).client.getContainer = jest.fn().mockImplementation(() => {
        const error: any = new Error('Not found');
        error.statusCode = 404;
        throw error;
      });

      const result = await dockerManager.stopSimulation('abc123');

      expect(result).toBe(false);
    });
  });

  describe('startSimulation', () => {
    it('should require configPath parameter', async () => {
      const mockContainer = {
        id: 'container123',
        start: jest.fn().mockResolvedValue(undefined),
      };

      (dockerManager as any).client.createContainer = jest.fn().mockResolvedValue(mockContainer);
      (dockerManager as any).findAvailablePort = jest.fn().mockResolvedValue(9001);
      (dockerManager as any).getSelfContainerId = jest.fn().mockResolvedValue(null);

      const result = await dockerManager.startSimulation({
        configPath: '/path/to/config.json',
        metricsPath: '/path/to/metrics.json',
        daemon: false,
      });

      expect(result.containerId).toBe('container123');
      expect(result.hostPort).toBe(9001);
      expect(mockContainer.start).toHaveBeenCalled();
    });

    it('should handle creation errors', async () => {
      (dockerManager as any).client.createContainer = jest
        .fn()
        .mockRejectedValue(new Error('Failed to create container'));
      (dockerManager as any).getSelfContainerId = jest.fn().mockResolvedValue(null);

      await expect(
        dockerManager.startSimulation({
          configPath: '/path/to/config.json',
          metricsPath: '/path/to/metrics.json',
          daemon: false,
        })
      ).rejects.toThrow();
    });
  });

  describe('stopAllSimulations', () => {
    it('should stop all running simulations', async () => {
      const mockContainers = [
        {
          Id: 'container1',
          Names: ['/autobox-sim-1'],
          State: 'running',
          Created: 1704067200,
        },
        {
          Id: 'container2',
          Names: ['/autobox-sim-2'],
          State: 'running',
          Created: 1704067200,
        },
      ];

      (dockerManager as any).client.listContainers = jest
        .fn()
        .mockResolvedValue(mockContainers);

      const mockContainer = {
        stop: jest.fn().mockResolvedValue(undefined),
        remove: jest.fn().mockResolvedValue(undefined),
      };

      (dockerManager as any).client.getContainer = jest.fn().mockReturnValue(mockContainer);

      const result = await dockerManager.stopAllSimulations();

      expect(result.total_stopped).toBe(2);
      expect(result.total_failed).toBe(0);
    });
  });

  describe('getContainerStatus', () => {
    it('should call inspect on container', async () => {
      const mockContainer = {
        inspect: jest.fn().mockResolvedValue({
          Id: 'container123abc',
          State: {
            Status: 'running',
            Running: true,
            StartedAt: '2024-01-01T00:00:00Z',
          },
          Config: {
            Image: 'autobox-engine:latest',
          },
        }),
      };

      (dockerManager as any).client.getContainer = jest.fn().mockReturnValue(mockContainer);

      const result = await dockerManager.getContainerStatus('container123');

      expect(mockContainer.inspect).toHaveBeenCalled();
      expect(result).toBeDefined();
    });

    it('should return null on error', async () => {
      (dockerManager as any).client.getContainer = jest.fn().mockImplementation(() => {
        const error: any = new Error('Not found');
        error.statusCode = 404;
        throw error;
      });

      const result = await dockerManager.getContainerStatus('nonexistent');

      expect(result).toBeNull();
    });
  });

  describe('getLogs', () => {
    it('should call logs method on container', async () => {
      const mockStream = {
        on: jest.fn((event, callback) => {
          if (event === 'data') {
            callback(Buffer.from('log line 1\nlog line 2\n'));
          }
          if (event === 'end') {
            callback();
          }
          return mockStream;
        }),
      };

      const mockContainer = {
        logs: jest.fn().mockResolvedValue(mockStream),
      };

      (dockerManager as any).client.getContainer = jest.fn().mockReturnValue(mockContainer);

      const result = await dockerManager.getLogs('container123', 10);

      expect(mockContainer.logs).toHaveBeenCalled();
      expect(result).toBeDefined();
    });
  });

  describe('instructAgent', () => {
    it('should attempt to send instruction to agent', async () => {
      const mockContainer = {
        inspect: jest.fn().mockResolvedValue({
          NetworkSettings: {
            Ports: {
              '9000/tcp': [{ HostPort: '9001' }],
            },
          },
        }),
      };

      (dockerManager as any).client.getContainer = jest.fn().mockReturnValue(mockContainer);

      const mockFetch = jest.fn().mockResolvedValue({
        ok: true,
        json: jest.fn().mockResolvedValue({ status: 'success' }),
      });
      global.fetch = mockFetch;

      const result = await dockerManager.instructAgent(
        'container123',
        'TestAgent',
        'Do something'
      );

      expect(mockContainer.inspect).toHaveBeenCalled();
      expect(result).toBeDefined();
    });
  });
});
