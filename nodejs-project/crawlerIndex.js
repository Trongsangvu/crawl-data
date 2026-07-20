"use strict";

/**
 * Crawler that collects all article URLs from shacho.osakazine.net album pages.
 * Converted from crawler_index.py (Scrapy -> axios + cheerio, since Scrapy
 * has no direct Node.js equivalent).
 */

const fs = require("fs");
const path = require("path");
const axios = require("axios");
const cheerio = require("cheerio");
const logUtils = require("./logUtils");

const BASE_URL = "https://shacho.osakazine.net";
const START_URL = `${BASE_URL}/album.html`;
// Lambda's filesystem is read-only except for /tmp
const OUTPUT_FILE = path.join("/data", "article_urls.json");
// const OUTPUT_FILE = path.join('/tmp', 'data', 'article_urls.json');
const USER_AGENT =
  "Mozilla/5.0 (Windows NT 10.0; Win64; x64) " +
  "AppleWebKit/537.36 (KHTML, like Gecko) " +
  "Chrome/124.0.0.0 Safari/537.36";

const DATE_PATTERN = /(\d{4}\/\d{2}\/\d{2})/;
const DOWNLOAD_DELAY_MS = 1000; // mirrors Scrapy's DOWNLOAD_DELAY

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

/** "2026/04/10" -> "2026-04-10", validating the date is real. */
function formatDate(title) {
  const m = DATE_PATTERN.exec(title);
  if (!m) return "";
  const [y, mo, d] = m[1].split("/").map(Number);
  const dt = new Date(Date.UTC(y, mo - 1, d));
  const valid =
    dt.getUTCFullYear() === y &&
    dt.getUTCMonth() === mo - 1 &&
    dt.getUTCDate() === d;
  if (!valid) return "";
  return `${String(y).padStart(4, "0")}-${String(mo).padStart(2, "0")}-${String(d).padStart(2, "0")}`;
}

function resolveUrl(base, href) {
  try {
    return new URL(href, base).toString();
  } catch (e) {
    return href;
  }
}

async function fetchPage(url) {
  return axios.get(url, {
    headers: { "User-Agent": USER_AGENT },
    timeout: 30000,
    validateStatus: () => true, // we check status.404 ourselves, like handle_httpstatus_list
  });
}

function parseAlbumPage($) {
  const articles = [];

  $("div.album div.album_frame").each((_, frame) => {
    const aTag = $(frame).find("div.album_image a").first();
    if (!aTag.length) return;

    const href = aTag.attr("href") || "";
    if (!href) return;

    const title = aTag.attr("title") || "";
    const date = formatDate(title);
    const url = href.startsWith("http") ? href : `${BASE_URL}/${href}`;

    articles.push({ url, date });
  });

  let nextHref = null;
  $("div.page_nav a").each((_, a) => {
    if (($(a).text() || "").includes("次へ")) {
      nextHref = $(a).attr("href") || "";
      return false; // break out of .each
    }
  });

  return { articles, nextHref };
}

/**
 * Walk album pages starting from START_URL, following "next page" links,
 * and save all discovered article URLs to outputFile.
 */
async function crawlIndex(outputFile = OUTPUT_FILE) {
  logUtils.crawler(`crawl_index: starting, output → ${outputFile}`);

  const allArticles = [];
  let currentUrl = START_URL;

  while (currentUrl) {
    const response = await fetchPage(currentUrl);

    if (response.status === 404) {
      logUtils.crawler("404 — stopping");
      break;
    }

    const $ = cheerio.load(response.data);
    const { articles, nextHref } = parseAlbumPage($);

    allArticles.push(...articles);
    logUtils.crawler(
      `${currentUrl}: ${articles.length} article(s) found (total ${allArticles.length})`,
    );

    if (nextHref) {
      logUtils.crawler(`following next page: ${nextHref}`);
      currentUrl = resolveUrl(currentUrl, nextHref);
      await sleep(DOWNLOAD_DELAY_MS);
    } else {
      logUtils.crawler("no next page — done");
      currentUrl = null;
    }
  }

  const records = allArticles
    .map((a) => ({
      url: a.url,
      date: a.date,
      status: "not_crawled",
      wp_post_id: null,
      wp_post_slug: null,
    }))
    .sort((a, b) => (a.date < b.date ? -1 : a.date > b.date ? 1 : 0));

  fs.mkdirSync(path.dirname(outputFile), { recursive: true });
  fs.writeFileSync(outputFile, JSON.stringify(records, null, 2), "utf-8");

  logUtils.crawler(
    `crawl_index: done — saved ${allArticles.length} URLs to ${outputFile}`,
  );

  return allArticles.map((a) => a.url);
}

module.exports = { crawlIndex, OUTPUT_FILE, START_URL, BASE_URL };

if (require.main === module) {
  crawlIndex().catch((e) => {
    logUtils.error(e.message);
    process.exitCode = 1;
  });
}
