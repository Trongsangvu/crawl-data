"use strict";

/**
 * Main crawl logic for the shacho-osaka crawler.
 * Converted from main.py (requests + BeautifulSoup -> axios + cheerio).
 */

const fs = require("fs");
const axios = require("axios");
const cheerio = require("cheerio");
const logUtils = require("./logUtils");
const { saveCeoInterview } = require("./appClient");
const { OUTPUT_FILE: ARTICLE_URLS_FILE } = require("./crawlerIndex");

const USER_AGENT =
  "Mozilla/5.0 (Windows NT 10.0; Win64; x64) " +
  "AppleWebKit/537.36 (KHTML, like Gecko) " +
  "Chrome/124.0.0.0 Safari/537.36";

/**
 * Parse a date string to a UTC Unix timestamp (seconds).
 * Handles ISO format (2026-04-10, 2026-04-10T00:31:07+09:00)
 * and Japanese format (2026年04月10日).
 */
function parseDateToTimestamp(dateStr) {
  if (!dateStr) return null;

  // Collapse whitespace/CRLF, mirroring the Python regex collapse
  let s = dateStr.replace(/[\r\n]+\s*/g, " ").trim();
  // Normalize Japanese format -> ISO
  s = s.replace(/(\d{4})年(\d{1,2})月(\d{1,2})日/, "$1-$2-$3");

  const isoWithOffset =
    /^(\d{4}-\d{2}-\d{2})T(\d{2}:\d{2}:\d{2})([+-]\d{2}:\d{2})?/;
  const spaceForm = /^(\d{4}-\d{2}-\d{2}) (\d{2}:\d{2})/;
  const dateOnly = /^(\d{4}-\d{2}-\d{2})/;

  let m = isoWithOffset.exec(s);
  if (m) {
    const iso = m[3] ? `${m[1]}T${m[2]}${m[3]}` : `${m[1]}T${m[2]}Z`;
    const t = Date.parse(iso);
    if (!Number.isNaN(t)) return Math.floor(t / 1000);
  }

  m = spaceForm.exec(s);
  if (m) {
    const t = Date.parse(`${m[1]}T${m[2]}:00Z`);
    if (!Number.isNaN(t)) return Math.floor(t / 1000);
  }

  m = dateOnly.exec(s);
  if (m) {
    const t = Date.parse(`${m[1]}T00:00:00Z`);
    if (!Number.isNaN(t)) return Math.floor(t / 1000);
  }

  logUtils.warning(`Could not parse date: ${JSON.stringify(dateStr)}`);
  return null;
}

function loadRecords(filePath) {
  const raw = fs.readFileSync(filePath, "utf-8");
  return JSON.parse(raw);
}

/** Fetch a single article page and return parsed title + content HTML. */
async function crawlArticle(url) {
  let response;
  try {
    response = await axios.get(url, {
      headers: { "User-Agent": USER_AGENT },
      timeout: 30000,
    });
  } catch (e) {
    logUtils.error(`Request failed for ${url}: ${e.message}`);
    return null;
  }

  const $ = cheerio.load(response.data);

  const titleTag = $('h3.title[itemprop="headline"]').first();
  const title = titleTag.length ? titleTag.text().trim() : "";

  const contentTag = $('div.main-post[itemprop="articleBody"]').first();
  const contentHtml = contentTag.length ? $.html(contentTag) : "";

  let imgAvatar = "";
  if (contentTag.length) {
    const firstImg = contentTag.find("img").first();
    if (firstImg.length) {
      imgAvatar = firstImg.attr("data-original") || firstImg.attr("src") || "";
      if (imgAvatar.startsWith("//")) {
        imgAvatar = `https:${imgAvatar}`;
      }
    }
  }

  // Prefer the RSS-style dc:date comment inside div.blogbody, fall back to
  // the visible entrydate span, exactly like the Python version.
  let date = "";
  const blogbody = $("div.blogbody").first();
  if (blogbody.length) {
    for (const node of blogbody.contents().toArray()) {
      if (node.type === "comment") {
        const m = /dc:date="([^"]+)"/.exec(node.data || "");
        if (m) {
          date = m[1]; // already ISO 8601, use as-is
          break;
        }
      }
    }
  }
  if (!date) {
    const dateTag = $('span.entrydate[itemprop="datePublished"]').first();
    const dateRaw = dateTag.length
      ? dateTag.attr("content") || dateTag.text().trim()
      : "";
    const ts = parseDateToTimestamp(dateRaw);
    date = ts ? new Date(ts * 1000).toISOString() : "";
  }

  const categories = [];
  const categoryTag = $("p#category-right").first();
  if (categoryTag.length) {
    categoryTag.find("a.aposted").each((_, a) => {
      const text = $(a).text().trim();
      if (text) categories.push(text);
    });
  }

  let companyName = "";
  let address = "";
  let officialSite = "";
  const h5Tag = $("h5").first();
  if (h5Tag.length) {
    // Company name is the direct text node(s) before the <span>
    companyName = h5Tag
      .contents()
      .toArray()
      .filter((n) => n.type === "text")
      .map((n) => $(n).text().trim())
      .join("")
      .trim();

    const spanTag = h5Tag.find("span").first();
    if (spanTag.length) {
      // Address is the text before the <br> / <a> inside the span
      address = spanTag
        .contents()
        .toArray()
        .filter((n) => n.type === "text")
        .map((n) => $(n).text().trim())
        .join("")
        .trim();

      const aTag = spanTag.find("a").first();
      if (aTag.length) {
        officialSite = (aTag.attr("href") || "").trim();
      }
    }
  }

  if (!title && !contentHtml) {
    logUtils.warning(`No title or content found for ${url}`);
    return null;
  }

  return {
    url,
    title,
    date,
    content: contentHtml,
    img_avatar: imgAvatar,
    categories,
    company_name: companyName,
    address,
    official_site: officialSite,
  };
}

/** Load records, crawl each not_crawled/failed URL, and save via API. */
async function runCrawl(recordsFile = ARTICLE_URLS_FILE) {
  const records = loadRecords(recordsFile);
  const pending = records.filter((r) =>
    ["not_crawled", "failed"].includes(r.status),
  );
  const total = pending.length;
  logUtils.info(`${total} URL(s) pending.`);

  for (let i = 0; i < pending.length; i++) {
    const record = pending[i];
    const index = i + 1;
    const url = record.url;
    logUtils.info(`[${index}/${total}] Crawling: ${url}`);

    const article = await crawlArticle(url);
    if (!article) {
      logUtils.warning(
        `[${index}/${total}] Skipping ${url} — no data returned.`,
      );
      continue;
    }

    await saveCeoInterview(article);
    logUtils.info(`[${index}/${total}] Saved: ${url}`);
  }

  logUtils.info("Done.");
}

module.exports = { runCrawl, crawlArticle, parseDateToTimestamp, loadRecords };

if (require.main === module) {
  runCrawl().catch((e) => {
    logUtils.error(e.message);
    process.exitCode = 1;
  });
}
