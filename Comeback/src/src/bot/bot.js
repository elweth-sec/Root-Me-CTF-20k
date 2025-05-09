const puppeteer = require("puppeteer");

// A remplacer par l'URL du challenge
const BASE_URL = "http://127.0.0.1:5000";

const delay = (time) => {
    return new Promise(resolve => setTimeout(resolve, time));
}

async function goto(url) {
	let browser
	try {
		browser = await puppeteer.launch({
			headless: true,
			ignoreHTTPSErrors: true,
			executablePath: "/usr/bin/chromium",
			args: [
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage',
                '--disable-accelerated-2d-canvas',
                '--disable-gpu',
                '--window-size=800x600',
				'--ignore-certificate-errors',
            ],
		});

		const page = await browser.newPage();

		await page.setViewport({ width: 1280, height: 720 });
		await page.setDefaultNavigationTimeout(5000);
		

		await page.goto(`${BASE_URL}/login`, { waitUntil: "networkidle2", timeout: 9999 });
		await page.type('#username', "admin");
  		await page.type('#password', "W00wwàwàwàw_Omgggggéééééç_So_H44Rd!&!&:O");
		await page.click('#submit')
	
		await delay(1000);
				
		await page.goto(url, { waitUntil: "networkidle2", timeout: 9999 });

		await delay(5000);

		browser.close();
		return;

	} catch (error){
		console.error(`Error visiting page: ${error}`);
	} finally {
		if (browser) {
            await browser.close();
        }
	}
}

if (process.argv.length === 2) {
    console.error("URL Missing");
    process.exit(1);
}

goto(process.argv[2]);
