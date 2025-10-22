import { z } from 'zod';

export const AgentConfigSchema = z.object({
  name: z.string(),
  description: z.string().optional(),
  role: z.string().optional(),
  backstory: z.string().optional(),
  llm: z.object({
    model: z.string().default('gpt-4o-mini'),
  }),
  instruction: z.string().optional(),
  context: z.string().optional().default(''),
});

export const SimulationConfigSchema = z.object({
  name: z.string(),
  description: z.string(),
  task: z.string(),
  timeout_seconds: z.number().default(300),
  shutdown_grace_period_seconds: z.number().default(5),
  evaluator: AgentConfigSchema,
  reporter: AgentConfigSchema,
  planner: AgentConfigSchema,
  orchestrator: AgentConfigSchema,
  workers: z.array(AgentConfigSchema),
  logging: z.object({
    verbose: z.boolean(),
    log_path: z.string(),
    log_file: z.string(),
  }),
});

export const TagConfigSchema = z.object({
  tag: z.string(),
  description: z.string(),
});

export const MetricTypeSchema = z.enum(['GAUGE', 'COUNTER', 'SUMMARY', 'HISTOGRAM']);

export const MetricConfigSchema = z.object({
  name: z.string(),
  description: z.string(),
  type: MetricTypeSchema,
  unit: z.string(),
  tags: z.array(TagConfigSchema),
});

export const MetricsConfigSchema = z.array(MetricConfigSchema);

export const ServerConfigSchema = z.object({
  port: z.number().default(9000),
});

export type AgentConfig = z.infer<typeof AgentConfigSchema>;
export type SimulationConfig = z.infer<typeof SimulationConfigSchema>;
export type MetricConfig = z.infer<typeof MetricConfigSchema>;
export type MetricsConfig = z.infer<typeof MetricsConfigSchema>;
export type TagConfig = z.infer<typeof TagConfigSchema>;
export type MetricType = z.infer<typeof MetricTypeSchema>;
export type ServerConfig = z.infer<typeof ServerConfigSchema>;

export interface SimulationStatus {
  id: string;
  name: string;
  status: string;
  configPath?: string;
  containerId?: string;
  created?: string;
  running?: boolean;
}

export interface ContainerStats {
  cpu_percent: number;
  memory_usage_mb: number;
  memory_limit_mb: number;
  memory_percent: number;
  network_rx_mb: number;
  network_tx_mb: number;
}

export interface SimulationMetrics {
  simulation_id: string;
  progress?: number;
  status?: string;
  current_step?: number;
  max_steps?: number;
  agent_count?: number;
  agents?: Record<
    string,
    {
      status: string;
      messages_sent: number;
      messages_received: number;
    }
  >;
  docker_stats?: ContainerStats;
  timestamp: number;
}
