/**
 * Utility helpers for colored console logging.
 * Converted from log_utils.py
 */

const BColors = {
  WARNING: "\x1b[93m",
  ENDC: "\x1b[0m",
  CRED: "\x1b[31m",
  C_BLUE: "\x1b[34m",
  C_GREEN: "\x1b[32m",
};

function warning(message) {
  console.log(`${BColors.WARNING}WARNING: ${message}${BColors.ENDC}`);
}

function error(message) {
  console.log(`${BColors.CRED}ERROR: ${message}${BColors.ENDC}`);
}

function info(message) {
  console.log(`${BColors.C_GREEN}INFO: ${message}${BColors.ENDC}`);
}

function crawler(message) {
  console.log(`${BColors.C_BLUE}[crawler] ${message}${BColors.ENDC}`);
}

function logger(fileName, functionName, message) {
  console.log(`${BColors.CRED}FILE: ${fileName}${BColors.ENDC}`);
  console.log(`${BColors.CRED}FUNCTION: ${functionName}${BColors.ENDC}`);
  console.log(`${BColors.CRED}ERROR: ${message}${BColors.ENDC}`);
  console.log(
    `${BColors.CRED}TIME: ${new Date().toISOString().replace("T", " ").slice(0, 19)}${BColors.ENDC}`,
  );
}

/**
 * Log an exception with file, function, and message extracted from the stack.
 */
function logException(err) {
  const stackLine = (err.stack || "").split("\n")[1] || "";
  logger(stackLine.trim() || "unknown", "unknown", err.message);
}

module.exports = { warning, error, info, crawler, logger, logException };
