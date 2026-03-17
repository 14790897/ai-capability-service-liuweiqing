export function getRequestMeta(context) {
  return {
    request_id: context.requestId,
    capability: context.capability,
    elapsed_ms: Math.max(0, Math.round(performance.now() - context.startedAt))
  };
}

export function buildSuccessResponse(data, meta) {
  return {
    ok: true,
    data,
    meta
  };
}

export function buildErrorResponse(error, meta) {
  return {
    ok: false,
    error,
    meta
  };
}
