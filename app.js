import crypto from 'node:crypto';

import express from 'express';

import { executeCapability } from './src/capabilities.js';
import { CapabilityError } from './src/capability-error.js';
import { buildErrorResponse, buildSuccessResponse, getRequestMeta } from './src/response.js';
import { capabilityRequestSchema } from './src/schemas.js';

const app = express();

app.use(express.json());

app.use((request, _response, next) => {
  request.context = {
    startedAt: performance.now(),
    requestId: crypto.randomUUID(),
    capability: 'unknown'
  };
  next();
});

app.get('/health', (_request, response) => {
  response.json({ status: 'ok' });
});

app.post('/v1/capabilities/run', (request, response, next) => {
  try {
    const parsed = capabilityRequestSchema.parse(request.body);
    request.context.requestId = parsed.request_id ?? request.context.requestId;
    request.context.capability = parsed.capability;

    const data = executeCapability(parsed.capability, parsed.input);
    const payload = buildSuccessResponse(data, getRequestMeta(request.context));

    console.info('capability_executed', payload.meta);
    response.status(200).json(payload);
  } catch (error) {
    next(error);
  }
});

app.use((error, request, response, _next) => {
  if (error instanceof SyntaxError && 'body' in error) {
    const payload = buildErrorResponse(
      {
        code: 'INVALID_JSON',
        message: 'Malformed JSON request body.',
        details: {}
      },
      getRequestMeta(request.context)
    );
    response.status(400).json(payload);
    return;
  }

  if (error instanceof CapabilityError) {
    const payload = buildErrorResponse(
      {
        code: error.code,
        message: error.message,
        details: error.details
      },
      getRequestMeta(request.context)
    );
    response.status(error.statusCode).json(payload);
    return;
  }

  console.error('unhandled_error', error);
  const payload = buildErrorResponse(
    {
      code: 'INTERNAL_ERROR',
      message: 'Unexpected server error.',
      details: {}
    },
    getRequestMeta(request.context)
  );
  response.status(500).json(payload);
});

export default app;
