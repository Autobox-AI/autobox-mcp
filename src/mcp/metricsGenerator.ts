import OpenAI from 'openai';
import type { SimulationConfig } from '../types/index.js';
import { logger } from '../utils/logger.js';

const SYSTEM_PROMPT = `<objective>
You are a smart Simulation Analyst. Your mission is to evaluate and analyse a simulation and design and define which metrics are relevant to measure the performance of the simulation and the system's behavior.
</objective>

<scope>
These are SOME general aspect of metrics:

1. Performance Metrics:
   • Resource Utilization: Tracks how efficiently resources are used by agents
   • Throughput: Measures the amount of work generated within a time frame
   • Response Time/Latency: Time taken to respond to events

2. Behavioral Metrics:
   • Agent Interaction Frequency: How often agents interact
   • Decision-Making Patterns: Choices agents make under conditions
   • Emergent Behaviors: Patterns arising from collective actions

3. Outcome Metrics:
   • Success Rate/Goal Achievement: How often goals are reached
   • System Stability: How stable the system remains over time
   • Resource Depletion/Regeneration: Resource consumption vs replenishment

4. Efficiency Metrics:
   • Cost Efficiency: Costs vs outputs generated
   • Time Efficiency: Time taken relative to expected time

5. Risk and Uncertainty Metrics:
   • Risk Exposure: Potential risks and impacts
   • Uncertainty Quantification: How uncertainty propagates

6. Adaptability and Resilience Metrics:
   • Adaptation Rate: How quickly agents adapt to changes
   • System Resilience: Ability to recover from disruptions

7. Satisfaction and Quality Metrics:
   • Agent Satisfaction: Overall satisfaction of agents
   • Quality of Output: Quality of outcomes produced
</scope>

<output>
You have to come up with STRUCTURED METRICS. This is a JSON array with a list of metrics that you consider relevant for the simulation you are analyzing.
Each metric should include: name (snake_case), description, type (COUNTER, GAUGE, or HISTOGRAM), unit, and tags array.

Your output MUST be only a valid JSON array of metric objects. Example format:
[
  {
    "name": "agent_interactions_total",
    "description": "Counts total interactions between agents",
    "type": "COUNTER",
    "unit": "interactions",
    "tags": [
      {
        "tag": "agent_name",
        "description": "Name of the interacting agent"
      }
    ]
  },
  {
    "name": "decision_time_seconds",
    "description": "Time taken to make decisions",
    "type": "HISTOGRAM",
    "unit": "seconds",
    "tags": []
  }
]
</output>`;

export async function generateMetricsWithLLM(
  config: SimulationConfig
): Promise<unknown[] | null> {
  const apiKey = process.env.OPENAI_API_KEY;
  if (!apiKey) {
    throw new Error('OPENAI_API_KEY environment variable not set');
  }

  const client = new OpenAI({ apiKey });

  let userPrompt = `Analyze this simulation and create relevant metrics:\n\n`;
  userPrompt += `Simulation Name: ${config.name}\n`;
  userPrompt += `Description: ${config.description}\n`;
  userPrompt += `Task: ${config.task}\n\n`;
  userPrompt += `Agents:\n`;

  for (const worker of config.workers) {
    userPrompt += `- ${worker.name}: ${worker.description || 'No role specified'}`;
    if (worker.context) {
      userPrompt += ` (Background: ${worker.context.substring(0, 200)}...)`;
    }
    userPrompt += '\n';
  }

  userPrompt += '\nCreate appropriate metrics to track this simulation\'s performance and outcomes.';

  try {
    const response = await client.chat.completions.create({
      model: 'gpt-4o-mini',
      messages: [
        { role: 'system', content: SYSTEM_PROMPT },
        { role: 'user', content: userPrompt },
      ],
      temperature: 0.7,
      max_tokens: 2000,
    });

    let metricsText = response.choices[0]?.message?.content?.trim();

    if (!metricsText) {
      logger.error('Empty response from LLM');
      return null;
    }

    if (metricsText.includes('```json')) {
      metricsText = metricsText.split('```json')[1].split('```')[0].trim();
    } else if (metricsText.includes('```')) {
      metricsText = metricsText.split('```')[1].split('```')[0].trim();
    }

    try {
      const metrics = JSON.parse(metricsText);
      return Array.isArray(metrics) ? metrics : null;
    } catch (parseError) {
      logger.error('Failed to parse LLM response as JSON:', parseError);
      logger.error('Response was:', metricsText);
      return null;
    }
  } catch (error) {
    logger.error('Error calling OpenAI API:', error);
    throw error;
  }
}
