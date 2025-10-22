import { DockerManager } from '../../src/docker/manager';

jest.mock('dockerode');

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
});
