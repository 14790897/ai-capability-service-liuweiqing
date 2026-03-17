import { ZodError } from 'zod';

import { CapabilityError } from './capability-error.js';
import { keywordsInputSchema, summaryInputSchema } from './schemas.js';

const STOPWORDS = new Set([
  'a',
  'an',
  'and',
  'are',
  'as',
  'at',
  'be',
  'by',
  'for',
  'from',
  'in',
  'is',
  'it',
  'of',
  'on',
  'or',
  'that',
  'the',
  'this',
  'to',
  'with'
]);

function normalizeText(text) {
  const normalized = text.replace(/\s+/g, ' ').trim();
  if (!normalized) {
    throw new CapabilityError({
      code: 'INVALID_INPUT',
      message: 'Input text cannot be empty after normalization.'
    });
  }
  return normalized;
}

function shorten(text, maxLength) {
  if (text.length <= maxLength) {
    return text;
  }
  return `${text.slice(0, Math.max(0, maxLength - 3)).trimEnd()}...`;
}

function mapValidationError(error, capability) {
  return new CapabilityError({
    code: 'INVALID_INPUT',
    message: `Invalid input for ${capability} capability.`,
    details: {
      validation_errors: error.issues
    }
  });
}

function runTextSummary(payload) {
  let parsed;

  try {
    parsed = summaryInputSchema.parse(payload);
  } catch (error) {
    if (error instanceof ZodError) {
      throw mapValidationError(error, 'text_summary');
    }
    throw error;
  }

  const text = normalizeText(parsed.text);
  const sentences = text.split(/(?<=[.!?。！？])\s+/).filter(Boolean);

  if (sentences.length === 0) {
    return { result: shorten(text, parsed.max_length) };
  }

  const collected = [];
  let currentLength = 0;

  for (const sentence of sentences) {
    const nextLength = currentLength + sentence.length + (collected.length > 0 ? 1 : 0);
    if (nextLength > parsed.max_length && collected.length > 0) {
      break;
    }

    collected.push(sentence);
    currentLength = nextLength;

    if (currentLength >= parsed.max_length) {
      break;
    }
  }

  return {
    result: shorten(collected.join(' ') || text, parsed.max_length)
  };
}

function runTextKeywords(payload) {
  let parsed;

  try {
    parsed = keywordsInputSchema.parse(payload);
  } catch (error) {
    if (error instanceof ZodError) {
      throw mapValidationError(error, 'text_keywords');
    }
    throw error;
  }

  const text = normalizeText(parsed.text.toLowerCase());
  const tokens = text.match(/[a-z]{2,}/g) ?? [];
  const counts = new Map();

  for (const token of tokens) {
    if (STOPWORDS.has(token)) {
      continue;
    }
    counts.set(token, (counts.get(token) ?? 0) + 1);
  }

  const keywords = [...counts.entries()]
    .sort((left, right) => right[1] - left[1] || left[0].localeCompare(right[0]))
    .slice(0, parsed.top_k)
    .map(([token]) => token);

  if (keywords.length === 0) {
    throw new CapabilityError({
      code: 'NO_KEYWORDS_FOUND',
      message: 'No extractable keywords were found in the input text.'
    });
  }

  return { result: keywords };
}

const capabilityRegistry = {
  text_summary: runTextSummary,
  text_keywords: runTextKeywords
};

export function executeCapability(capability, payload) {
  const handler = capabilityRegistry[capability];
  if (!handler) {
    throw new CapabilityError({
      code: 'UNSUPPORTED_CAPABILITY',
      message: `Unsupported capability: ${capability}`,
      statusCode: 404,
      details: {
        supported_capabilities: Object.keys(capabilityRegistry).sort()
      }
    });
  }

  return handler(payload);
}
