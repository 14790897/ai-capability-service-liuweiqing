import request from 'supertest';
import { describe, expect, it } from 'vitest';

import app from '../app.js';

describe('AI capability service', () => {
  it('returns health status', async () => {
    const response = await request(app).get('/health');

    expect(response.statusCode).toBe(200);
    expect(response.body).toEqual({ status: 'ok' });
  });

  it('runs text_summary successfully', async () => {
    const response = await request(app)
      .post('/v1/capabilities/run')
      .send({
        capability: 'text_summary',
        input: {
          text: 'Express deploys well on Vercel. This service provides a unified API. The implementation stays intentionally small.',
          max_length: 70
        },
        request_id: 'summary-test-1'
      });

    expect(response.statusCode).toBe(200);
    expect(response.body.ok).toBe(true);
    expect(response.body.meta.request_id).toBe('summary-test-1');
    expect(response.body.meta.capability).toBe('text_summary');
    expect(response.body.data.result.length).toBeLessThanOrEqual(70);
  });

  it('runs text_keywords successfully', async () => {
    const response = await request(app)
      .post('/v1/capabilities/run')
      .send({
        capability: 'text_keywords',
        input: {
          text: 'Simple APIs improve delivery speed and service quality. APIs help service teams move faster.',
          top_k: 3
        }
      });

    expect(response.statusCode).toBe(200);
    expect(response.body.ok).toBe(true);
    expect(response.body.data.result).toHaveLength(3);
  });

  it('returns stable error for unsupported capability', async () => {
    const response = await request(app)
      .post('/v1/capabilities/run')
      .send({
        capability: 'image_generation',
        input: {
          prompt: 'hello'
        }
      });

    expect(response.statusCode).toBe(404);
    expect(response.body.ok).toBe(false);
    expect(response.body.error.code).toBe('UNSUPPORTED_CAPABILITY');
  });

  it('returns validation error for invalid capability input', async () => {
    const response = await request(app)
      .post('/v1/capabilities/run')
      .send({
        capability: 'text_summary',
        input: {
          text: 'abc',
          max_length: 1
        }
      });

    expect(response.statusCode).toBe(400);
    expect(response.body.ok).toBe(false);
    expect(response.body.error.code).toBe('INVALID_INPUT');
  });
});