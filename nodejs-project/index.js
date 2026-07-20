/**
 * AWS Lambda entry point.
 * Converted from lambda_function.py
 */

const { crawlIndex } = require("./crawlerIndex");
const { runCrawl } = require("./mainCrawl");

exports.handler = async (event, context) => {
  try {
    await crawlIndex();
    await runCrawl();

    return {
      statusCode: 200,
      body: JSON.stringify({
        message: "Crawler completed successfully",
      }),
    };
  } catch (e) {
    console.error(`Error: ${e.message}`);
    throw e;
  }
};

// Allows running locally with `node index.js`, same as `lambda_function.py`
// running standalone. AWS Lambda itself never hits this branch — it calls
// exports.handler directly.
if (require.main === module) {
  exports
    .handler({}, {})
    .then((res) => console.log("Done:", res))
    .catch((e) => {
      console.error(e);
      process.exitCode = 1;
    });
}
