import { generateMetricsWithLLM } from '../../src/mcp/metricsGenerator';
import OpenAI from 'openai';
import type { SimulationConfig } from '../../src/types/index';

jest.mock('openai');

describe('MetricsGenerator', () => {
  let mockOpenAI: jest.Mocked<OpenAI>;
  const originalEnv = process.env.OPENAI_API_KEY;

  beforeEach(() => {
    jest.clearAllMocks();
    process.env.OPENAI_API_KEY = 'test-api-key';

    mockOpenAI = {
      chat: {
        completions: {
          create: jest.fn(),
        },
      },
    } as any;

    (OpenAI as jest.MockedClass<typeof OpenAI>).mockImplementation(() => mockOpenAI);
  });

  afterEach(() => {
    process.env.OPENAI_API_KEY = originalEnv;
  });

  const mockConfig: SimulationConfig = {
    name: 'test-simulation',
    description: 'A test simulation',
    task: 'Test task description',
    timeout_seconds: 300,
    shutdown_grace_period_seconds: 5,
    evaluator: { name: 'EVALUATOR', llm: { model: 'gpt-4o-mini' }, context: '' },
    reporter: { name: 'REPORTER', llm: { model: 'gpt-4o-mini' }, context: '' },
    planner: { name: 'PLANNER', llm: { model: 'gpt-4o-mini' }, context: '' },
    orchestrator: { name: 'ORCHESTRATOR', llm: { model: 'gpt-4o-mini' }, context: '' },
    workers: [
      {
        name: 'Worker1',
        description: 'Test worker',
        context: 'Worker context information',
        llm: { model: 'gpt-4o-mini' },
      },
    ],
    logging: {
      verbose: false,
      log_path: 'logs',
      log_file: 'test.log',
    },
  };

  describe('generateMetricsWithLLM', () => {
    it('should throw error when OPENAI_API_KEY is not set', async () => {
      delete process.env.OPENAI_API_KEY;

      await expect(generateMetricsWithLLM(mockConfig)).rejects.toThrow(
        'OPENAI_API_KEY environment variable not set'
      );
    });

    it('should generate metrics successfully', async () => {
      const expectedMetrics = [
        {
          name: 'agent_interactions_total',
          description: 'Counts total interactions between agents',
          type: 'COUNTER',
          unit: 'interactions',
          tags: [],
        },
      ];

      mockOpenAI.chat.completions.create = jest.fn().mockResolvedValue({
        choices: [
          {
            message: {
              content: JSON.stringify(expectedMetrics),
            },
          },
        ],
      });

      const result = await generateMetricsWithLLM(mockConfig);

      expect(result).toEqual(expectedMetrics);
      expect(mockOpenAI.chat.completions.create).toHaveBeenCalledWith(
        expect.objectContaining({
          model: 'gpt-4o-mini',
          temperature: 0.7,
          max_tokens: 2000,
        })
      );
    });

    it('should handle JSON wrapped in markdown code blocks', async () => {
      const expectedMetrics = [
        {
          name: 'test_metric',
          description: 'Test metric',
          type: 'GAUGE',
          unit: 'count',
          tags: [],
        },
      ];

      mockOpenAI.chat.completions.create = jest.fn().mockResolvedValue({
        choices: [
          {
            message: {
              content: '```json\n' + JSON.stringify(expectedMetrics) + '\n```',
            },
          },
        ],
      });

      const result = await generateMetricsWithLLM(mockConfig);

      expect(result).toEqual(expectedMetrics);
    });

    it('should handle JSON wrapped in generic code blocks', async () => {
      const expectedMetrics = [
        {
          name: 'test_metric',
          description: 'Test metric',
          type: 'HISTOGRAM',
          unit: 'seconds',
          tags: [],
        },
      ];

      mockOpenAI.chat.completions.create = jest.fn().mockResolvedValue({
        choices: [
          {
            message: {
              content: '```\n' + JSON.stringify(expectedMetrics) + '\n```',
            },
          },
        ],
      });

      const result = await generateMetricsWithLLM(mockConfig);

      expect(result).toEqual(expectedMetrics);
    });

    it('should return null on empty response', async () => {
      mockOpenAI.chat.completions.create = jest.fn().mockResolvedValue({
        choices: [
          {
            message: {
              content: '',
            },
          },
        ],
      });

      const result = await generateMetricsWithLLM(mockConfig);

      expect(result).toBeNull();
    });

    it('should return null on invalid JSON', async () => {
      mockOpenAI.chat.completions.create = jest.fn().mockResolvedValue({
        choices: [
          {
            message: {
              content: 'This is not valid JSON',
            },
          },
        ],
      });

      const result = await generateMetricsWithLLM(mockConfig);

      expect(result).toBeNull();
    });

    it('should return null when response is not an array', async () => {
      mockOpenAI.chat.completions.create = jest.fn().mockResolvedValue({
        choices: [
          {
            message: {
              content: JSON.stringify({ not: 'an array' }),
            },
          },
        ],
      });

      const result = await generateMetricsWithLLM(mockConfig);

      expect(result).toBeNull();
    });

    it('should throw error on OpenAI API failure', async () => {
      mockOpenAI.chat.completions.create = jest
        .fn()
        .mockRejectedValue(new Error('API Error'));

      await expect(generateMetricsWithLLM(mockConfig)).rejects.toThrow('API Error');
    });

    it('should include simulation details in prompt', async () => {
      mockOpenAI.chat.completions.create = jest.fn().mockResolvedValue({
        choices: [
          {
            message: {
              content: '[]',
            },
          },
        ],
      });

      await generateMetricsWithLLM(mockConfig);

      const callArgs = mockOpenAI.chat.completions.create.mock.calls[0][0];
      const userMessage = callArgs.messages.find((m: any) => m.role === 'user');

      expect(userMessage.content).toContain(mockConfig.name);
      expect(userMessage.content).toContain(mockConfig.description);
      expect(userMessage.content).toContain(mockConfig.task);
      expect(userMessage.content).toContain('Worker1');
    });
  });
});
