import { RealtimeLLMClient } from '../openai/realtime_client.ts';
import { EventHandler } from '../queue/consumer.ts';

interface Event {
  type: string;
  timestamp: string;
  data: Record<string, unknown>;
}

interface Decision {
  actionType: string;
  confidence: number;
  reasoning?: string[];
  details: Record<string, unknown>;
}

export class AgenticController implements EventHandler {
  private readonly llmClient: RealtimeLLMClient;
  private readonly maxRetries: number;
  private readonly retryDelay: number;

  constructor(
    llmClient: RealtimeLLMClient,
    maxRetries: number = 3,
    retryDelay: number = 1000
  ) {
    this.llmClient = llmClient;
    this.maxRetries = maxRetries;
    this.retryDelay = retryDelay;
  }

  async processEvent(rawEvent: Record<string, unknown>): Promise<void> {
    // Validate and convert raw event to typed Event
    const event = this.validateEvent(rawEvent);
    await this.processTypedEvent(event);
  }

  private validateEvent(rawEvent: Record<string, unknown>): Event {
    if (!rawEvent || typeof rawEvent !== 'object') {
      throw new Error('Event must be an object');
    }

    if (!rawEvent.type || typeof rawEvent.type !== 'string') {
      throw new Error('Event must have a string type');
    }

    if (!rawEvent.timestamp || typeof rawEvent.timestamp !== 'string') {
      throw new Error('Event must have a string timestamp');
    }

    if (!rawEvent.data || typeof rawEvent.data !== 'object') {
      throw new Error('Event must have a data object');
    }

    return {
      type: rawEvent.type,
      timestamp: rawEvent.timestamp,
      data: rawEvent.data as Record<string, unknown>,
    };
  }

  private async processTypedEvent(event: Event): Promise<Decision> {
    // Format the prompt based on event type and data
    const prompt = this.formatPrompt(event);

    try {
      // Get streaming response from LLM
      const generator = await this.llmClient.streamText(prompt);
      let fullResponse = '';

      // Collect the complete response
      for await (const chunk of generator) {
        fullResponse += chunk;
      }

      // Parse the response into a decision
      return this.parseResponse(fullResponse);
    } catch (error) {
      throw new Error(`Failed to process event: ${error instanceof Error ? error.message : String(error)}`);
    }
  }

  private formatPrompt(event: Event): string {
    // Build context-aware prompt based on event type
    let prompt = `Analyze the following ${event.type} event and determine the appropriate action:\n\n`;
    prompt += `Event Type: ${event.type}\n`;
    prompt += `Timestamp: ${event.timestamp}\n`;
    prompt += `Data: ${JSON.stringify(event.data, null, 2)}\n\n`;

    // Add type-specific instructions
    switch (event.type) {
      case 'market':
        prompt += 'Consider market indicators, trends, and risk factors. Determine if a trade action is warranted.\n';
        break;
      case 'code':
        prompt += 'Analyze code for issues, potential improvements, or necessary updates.\n';
        break;
      default:
        prompt += 'Analyze the event data and determine if any action is needed.\n';
    }

    prompt += '\nProvide your response in the following format:\n';
    prompt += 'Action: [ACTION_TYPE]\n';
    prompt += 'Confidence: [0.0-1.0]\n';
    prompt += 'Reasoning:\n1. [First reason]\n2. [Second reason]\n3. [Third reason]\n';
    prompt += 'Details:\n[JSON object with action-specific details]\n';

    return prompt;
  }

  private parseResponse(response: string): Decision {
    try {
      // Extract action type
      const actionMatch = response.match(/Action:\s*(\w+)/);
      if (!actionMatch) throw new Error('No action found in response');
      const actionType = actionMatch[1];

      // Extract confidence
      const confidenceMatch = response.match(/Confidence:\s*(0\.\d+|1\.0|1|0)/);
      if (!confidenceMatch) throw new Error('No confidence score found in response');
      const confidence = parseFloat(confidenceMatch[1]);

      // Extract reasoning
      const reasoningMatch = response.match(/Reasoning:\n((?:(?:\d+\.\s*[^\n]+\n?)+))/);
      const reasoning = reasoningMatch
        ? reasoningMatch[1]
            .split('\n')
            .filter(line => line.trim())
            .map(line => line.replace(/^\d+\.\s*/, '').trim())
        : undefined;

      // Extract details
      const detailsMatch = response.match(/Details:\n({[\s\S]*})/);
      if (!detailsMatch) throw new Error('No details found in response');
      const details = JSON.parse(detailsMatch[1]);

      return {
        actionType,
        confidence,
        reasoning,
        details,
      };
    } catch (error) {
      throw new Error(`Failed to parse LLM response: ${error instanceof Error ? error.message : String(error)}`);
    }
  }
}
