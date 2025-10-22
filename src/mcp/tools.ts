import { Tool } from '@modelcontextprotocol/sdk/types.js';

export const tools: Tool[] = [
  {
    name: 'list_simulations',
    description: 'List all simulations (running and completed)',
    inputSchema: {
      type: 'object',
      properties: {},
    },
  },
  {
    name: 'start_simulation',
    description: 'Start a new simulation from a configuration file',
    inputSchema: {
      type: 'object',
      properties: {
        config_name: {
          type: 'string',
          description: "Name of the simulation config (e.g., 'summer_vacation')",
        },
        custom_config: {
          type: 'object',
          description: 'Optional: Custom simulation config object instead of using a file',
        },
        daemon: {
          type: 'boolean',
          description: 'Optional: Run in daemon mode (keeps server alive after simulation completes, default: false)',
          default: false,
        },
      },
    },
  },
  {
    name: 'stop_simulation',
    description: 'Stop a running simulation gracefully',
    inputSchema: {
      type: 'object',
      properties: {
        simulation_id: {
          type: 'string',
          description: 'ID of the simulation to stop',
        },
      },
      required: ['simulation_id'],
    },
  },
  {
    name: 'get_simulation_status',
    description: 'Get detailed status of a specific simulation',
    inputSchema: {
      type: 'object',
      properties: {
        simulation_id: {
          type: 'string',
          description: 'ID of the simulation',
        },
      },
      required: ['simulation_id'],
    },
  },
  {
    name: 'get_simulation_logs',
    description: 'Get logs from a simulation container',
    inputSchema: {
      type: 'object',
      properties: {
        simulation_id: {
          type: 'string',
          description: 'ID of the simulation',
        },
        tail: {
          type: 'number',
          description: 'Number of lines to retrieve from the end (default: 100)',
          default: 100,
        },
      },
      required: ['simulation_id'],
    },
  },
  {
    name: 'list_available_configs',
    description: 'List all available simulation configuration templates',
    inputSchema: {
      type: 'object',
      properties: {},
    },
  },
  {
    name: 'get_simulation_metrics',
    description: 'Get metrics from a running simulation (progress, agent interactions, API status)',
    inputSchema: {
      type: 'object',
      properties: {
        simulation_id: {
          type: 'string',
          description: 'ID of the simulation',
        },
        include_docker_stats: {
          type: 'boolean',
          description: 'Include Docker container stats (CPU, memory, network)',
          default: true,
        },
      },
      required: ['simulation_id'],
    },
  },
  {
    name: 'create_simulation_config',
    description: 'Create a new simulation configuration with AI assistance',
    inputSchema: {
      type: 'object',
      properties: {
        name: {
          type: 'string',
          description: 'Name for the simulation',
        },
        description: {
          type: 'string',
          description: 'Description of what the simulation should accomplish',
        },
        agents: {
          type: 'array',
          description: 'List of agent descriptions',
          items: {
            type: 'object',
            properties: {
              name: { type: 'string' },
              role: { type: 'string' },
              backstory: { type: 'string' },
            },
          },
        },
        max_steps: {
          type: 'number',
          description: 'Maximum number of simulation steps (default: 100)',
          default: 100,
        },
        timeout_seconds: {
          type: 'number',
          description: 'Timeout in seconds (default: 300)',
          default: 300,
        },
      },
      required: ['name', 'description'],
    },
  },
  {
    name: 'stop_all_simulations',
    description: 'Stop ALL running simulations (terminate all autobox Docker containers)',
    inputSchema: {
      type: 'object',
      properties: {},
    },
  },
  {
    name: 'create_simulation_metrics',
    description: 'Create metrics configuration for a simulation using AI assistance or custom metrics',
    inputSchema: {
      type: 'object',
      properties: {
        simulation_name: {
          type: 'string',
          description: 'Name of the simulation (must match an existing config)',
        },
        use_llm: {
          type: 'boolean',
          description: 'Whether to use LLM to generate metrics (default: true)',
          default: true,
        },
        custom_metrics: {
          type: 'array',
          description: 'Custom metrics (if use_llm is false)',
          items: {
            type: 'object',
            properties: {
              name: { type: 'string' },
              description: { type: 'string' },
              type: {
                type: 'string',
                enum: ['COUNTER', 'GAUGE', 'HISTOGRAM', 'SUMMARY'],
              },
              unit: { type: 'string' },
              tags: {
                type: 'array',
                items: { type: 'object' },
              },
            },
          },
        },
      },
      required: ['simulation_name'],
    },
  },
  {
    name: 'instruct_agent',
    description: 'Send instructions to a specific agent in an ongoing simulation',
    inputSchema: {
      type: 'object',
      properties: {
        simulation_id: {
          type: 'string',
          description: 'ID of the running simulation',
        },
        agent_name: {
          type: 'string',
          description: 'Name of the agent to instruct',
        },
        instruction: {
          type: 'string',
          description: 'Instruction to send to the agent',
        },
      },
      required: ['simulation_id', 'agent_name', 'instruction'],
    },
  },
  {
    name: 'delete_simulation',
    description: 'Delete a simulation configuration and its associated metrics files',
    inputSchema: {
      type: 'object',
      properties: {
        simulation_name: {
          type: 'string',
          description: 'Name of the simulation to delete (without file extension)',
        },
      },
      required: ['simulation_name'],
    },
  },
  {
    name: 'ping_simulation',
    description: 'Check if a simulation API is responsive (basic connectivity test)',
    inputSchema: {
      type: 'object',
      properties: {
        simulation_id: {
          type: 'string',
          description: 'ID of the simulation',
        },
      },
      required: ['simulation_id'],
    },
  },
  {
    name: 'get_simulation_health',
    description: 'Get detailed health status of a simulation from its API',
    inputSchema: {
      type: 'object',
      properties: {
        simulation_id: {
          type: 'string',
          description: 'ID of the simulation',
        },
      },
      required: ['simulation_id'],
    },
  },
  {
    name: 'get_simulation_execution_status',
    description: 'Get the current execution status of a simulation (progress, phase, agents state)',
    inputSchema: {
      type: 'object',
      properties: {
        simulation_id: {
          type: 'string',
          description: 'ID of the simulation',
        },
      },
      required: ['simulation_id'],
    },
  },
  {
    name: 'abort_simulation',
    description: 'Gracefully abort a running simulation (different from Docker stop - allows cleanup)',
    inputSchema: {
      type: 'object',
      properties: {
        simulation_id: {
          type: 'string',
          description: 'ID of the simulation to abort',
        },
      },
      required: ['simulation_id'],
    },
  },
  {
    name: 'get_simulation_info',
    description: 'Get simulation information and metadata from its API',
    inputSchema: {
      type: 'object',
      properties: {
        simulation_id: {
          type: 'string',
          description: 'ID of the simulation',
        },
      },
      required: ['simulation_id'],
    },
  },
  {
    name: 'get_simulation_api_spec',
    description: 'Get the OpenAPI/Swagger specification of a simulation API',
    inputSchema: {
      type: 'object',
      properties: {
        simulation_id: {
          type: 'string',
          description: 'ID of the simulation',
        },
      },
      required: ['simulation_id'],
    },
  },
];
