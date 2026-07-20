"use strict";

/**
 * API client for saving crawled CEO interview data.
 * Converted from app_client.py (pydantic model -> plain JS validation).
 */

const axios = require("axios");
const logUtils = require("./logUtils");
const { APIConfig } = require("./constants");

const CEO_INTERVIEWS_ENDPOINT = `${APIConfig.API_BASE_URL}/api/v1/ceo-interviews/`;

/**
 * Validate/normalize the article payload, mirroring the Python
 * CeoInterviewCreateRequest pydantic model.
 */
function buildPayload(article) {
  if (!article.url || typeof article.url !== "string") {
    throw new Error(`Missing or invalid url: ${article.url}`);
  }
  try {
    // eslint-disable-next-line no-new
    new URL(article.url); // throws if not a valid absolute URL
  } catch (e) {
    throw new Error(`url is not a valid http(s) URL: ${article.url}`);
  }

  return {
    url: article.url,
    posted_date: article.date ?? null,
    title: article.title ?? null,
    content_html: article.content ?? null,
    img_avatar: article.img_avatar ?? null,
    categories: article.categories ?? [],
    company_name: article.company_name ?? null,
    address: article.address ?? null,
    official_site: article.official_site ?? null,
  };
}

async function saveCeoInterview(article) {
  let payload;
  try {
    payload = buildPayload(article);
  } catch (e) {
    logUtils.error(`Invalid payload for ${article.url}: ${e.message}`);
    return false;
  }

  console.log("===== API DEBUG =====");
  console.log("ENDPOINT:", CEO_INTERVIEWS_ENDPOINT);
  console.log("API KEY:", APIConfig.API_KEY);
  console.log("PAYLOAD:", JSON.stringify(payload, null, 2));
  console.log("=====================");

  try {
    const response = await axios.post(CEO_INTERVIEWS_ENDPOINT, payload, {
      headers: { "x-api-key": APIConfig.API_KEY },
      timeout: 30000,
    });

    logUtils.info(`Saved ${article.url} (${response.status})`);
    return true;
  } catch (e) {
    if (e.response) {
      logUtils.error(
        `Failed ${article.url} (${e.response.status}): ${JSON.stringify(e.response.data)}`,
      );
    } else {
      logUtils.error(`Failed ${article.url}: ${e.message}`);
    }

    return null;
  }
}

module.exports = { saveCeoInterview, CEO_INTERVIEWS_ENDPOINT };
