import { chromium } from "playwright-core";

const baseUrl = (process.env.RESPONSIVE_TEST_BASE_URL ?? "http://127.0.0.1:3000").replace(/\/$/, "");
const executablePath = process.env.CHROME_PATH ?? "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe";

const viewports = [
  { name: "mobile", width: 390, height: 844 },
  { name: "tablet", width: 768, height: 1024 },
  { name: "laptop", width: 1366, height: 768 },
  { name: "desktop", width: 1920, height: 1080 },
];

const routes = [
  "/",
  "/about",
  "/contact",
  "/gallery",
  "/services",
  "/shop",
  "/book",
  "/cart",
  "/login",
  "/register",
  "/account",
  "/management",
  "/management/reports",
  "/pos",
];

const browser = await chromium.launch({ executablePath, headless: true });
const failures = [];

async function navigate(page, url) {
  try {
    return await page.goto(url, { waitUntil: "domcontentloaded", timeout: 30_000 });
  } catch (error) {
    if (!String(error).includes("ERR_ABORTED")) throw error;
    await page.waitForTimeout(250);
    return page.goto(url, { waitUntil: "domcontentloaded", timeout: 30_000 });
  }
}

async function inspectLayout(page) {
  for (let attempt = 0; attempt < 3; attempt += 1) {
    try {
      await page.waitForLoadState("domcontentloaded", { timeout: 5_000 }).catch(() => {});
      // Protected routes redirect on the client once the session check finishes.
      // Waiting for the final page landmark prevents inspecting the transient,
      // unmounted document between the original route and its login redirect.
      await page.locator("main").first().waitFor({ state: "attached", timeout: 5_000 }).catch(() => {});
      const result = await page.evaluate(() => {
        const root = document.documentElement;
        const body = document.body;
        const viewportWidth = window.innerWidth;
        const overflow = Math.max(root.scrollWidth, body.scrollWidth) - viewportWidth;
        const clipped = [...document.querySelectorAll("main *")]
          .filter((element) => {
            const style = getComputedStyle(element);
            if (style.position === "fixed" || style.position === "absolute") return false;
            let ancestor = element;
            while (ancestor && ancestor !== document.documentElement) {
              const overflowX = getComputedStyle(ancestor).overflowX;
              if (overflowX === "auto" || overflowX === "scroll") return false;
              ancestor = ancestor.parentElement;
            }
            const rect = element.getBoundingClientRect();
            return rect.width > 0 && (rect.left < -2 || rect.right > viewportWidth + 2);
          })
          .slice(0, 5)
          .map((element) => ({
            tag: element.tagName.toLowerCase(),
            className: typeof element.className === "string" ? element.className : "",
            text: element.textContent?.trim().slice(0, 50) ?? "",
          }));

        return {
          overflow,
          clipped,
          hasMain: Boolean(document.querySelector("main")),
          title: document.title,
        };
      });
      if (!result.hasMain && attempt < 2) {
        await page.waitForTimeout(500);
        continue;
      }
      return result;
    } catch (error) {
      if (!String(error).includes("Execution context was destroyed") || attempt === 2) throw error;
      await page.waitForTimeout(350);
    }
  }
}

try {
  for (const viewport of viewports) {
    const context = await browser.newContext({ viewport });
    const page = await context.newPage();

    await navigate(page, `${baseUrl}/`);
    await page.waitForTimeout(350);
    const menuToggle = page.locator(".mobile-menu-toggle");
    const primaryNav = page.locator(".primary-nav");
    if (viewport.width <= 768) {
      if (!(await menuToggle.isVisible())) failures.push(`${viewport.name}: mobile menu toggle is hidden`);
      if (await primaryNav.isVisible()) failures.push(`${viewport.name}: desktop navigation remains visible`);
      await menuToggle.click();
      if (!(await page.locator("#mobile-navigation").isVisible())) {
        failures.push(`${viewport.name}: mobile navigation does not open`);
      }
      await page.keyboard.press("Escape");
      if (await page.locator("#mobile-navigation").isVisible()) {
        failures.push(`${viewport.name}: mobile navigation does not close with Escape`);
      }
    } else {
      if (await menuToggle.isVisible()) failures.push(`${viewport.name}: mobile menu toggle remains visible`);
      if (!(await primaryNav.isVisible())) failures.push(`${viewport.name}: primary navigation is hidden`);
    }
    await page.close();

    for (const route of routes) {
      // Isolate each route so an authentication redirect from one protected
      // page cannot race the navigation to the next route.
      const routePage = await context.newPage();
      const response = await navigate(routePage, `${baseUrl}${route}`);
      await routePage.waitForTimeout(350);
      if (!response || response.status() >= 500) {
        failures.push(`${viewport.name} ${route}: HTTP ${response?.status() ?? "no response"}`);
        await routePage.close();
        continue;
      }

      const result = await inspectLayout(routePage);

      if (!result.hasMain) failures.push(`${viewport.name} ${route}: missing main landmark`);
      if (result.overflow > 2) {
        failures.push(`${viewport.name} ${route}: ${result.overflow}px horizontal page overflow`);
      }
      if (result.clipped.length) {
        failures.push(`${viewport.name} ${route}: clipped content ${JSON.stringify(result.clipped)}`);
      }
      if (!result.title) failures.push(`${viewport.name} ${route}: missing document title`);
      process.stdout.write(`PASS ${viewport.name.padEnd(7)} ${route}\n`);
      await routePage.close();
    }

    await context.close();
  }
} finally {
  await browser.close();
}

if (failures.length) {
  console.error("\nResponsive layout failures:\n" + failures.map((item) => `- ${item}`).join("\n"));
  process.exit(1);
}

console.log(`\nResponsive checks passed for ${routes.length} routes across ${viewports.length} viewports.`);
