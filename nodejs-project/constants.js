/**
 * Configuration for the internal API integration.
 * Converted from constants.py
 */
const APIConfig = {
  API_BASE_URL: process.env.API_BASE_URL || "http://127.0.0.1:8000",
  API_KEY: process.env.API_KEY || "71df333a-9593-4a84-9e46-adc722bb9758",
};

module.exports = { APIConfig };
