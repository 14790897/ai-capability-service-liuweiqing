export class CapabilityError extends Error {
  constructor({ code, message, statusCode = 400, details = {} }) {
    super(message);
    this.name = 'CapabilityError';
    this.code = code;
    this.statusCode = statusCode;
    this.details = details;
  }
}
