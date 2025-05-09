const express = require('express');
const app = express();
const path = require('path');
const cookieParser = require('cookie-parser');
const puppeteer = require('puppeteer');
const cors = require("cors");

app.use(express.static('public'));
app.use(cookieParser());
app.use(express.json());
app.use(cors({
    origin: '*',
    credentials: true
}));

app.get('/', (req, res) => {
    res.sendFile(path.join(__dirname, 'public/index.html'));
});

function checkAdminCookie(req, res, next) {
    const adminCookie = req.cookies.admin;
    if (adminCookie === 'YesIMTh3Admiiiin_And_U_Cant_4ccess_HEEERE') {
        next();
    } else {
        res.status(403).send('Forbidden');
    }
}

app.get('/admin', checkAdminCookie, (req, res) => {
    res.send('RM{Hmm_THis_XSS_Was_N0t_As_Usu4l}');
});

app.get('/report', (req, res) => {
    res.sendFile(path.join(__dirname, 'public/report.html'));
});

app.post('/api/report', async (req, res) => {
    const { url } = req.body;

    if (!url) {
        return res.status(400).json({ success: false, message: 'URL is required' });
    }

    console.log(`Visiting ${url}`);

    try {
        const browser = await puppeteer.launch({
            headless: 'new',
            executablePath: '/usr/bin/google-chrome',
            args: [
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage',
                '--window-size=1280,720'
            ],
            defaultViewport: null,
            slowMo: 100
        });

        const page = await browser.newPage();

        console.log('Setting admin cookie...');
        await page.setCookie({
            name: 'admin',
            value: 'YesIMTh3Admiiiin_And_U_Cant_4ccess_HEEERE',
            domain: '127.0.0.1',
            path: '/',
            httpOnly: true,
            sameSite: 'Lax',
            secure: false
        });

        console.log('Navigating to http://127.0.0.1:3000...');
        await page.goto('http://127.0.0.1:3000', {
            waitUntil: 'networkidle2',
            timeout: 30000
        });

        const cookies = await page.cookies();
        console.log('Cookies after first nav:', cookies);

        console.log('Navigating to user-provided URL...');
        const response = await page.goto(url, {
            waitUntil: 'networkidle2',
            timeout: 30000
        });

        console.log('Waiting...');
        await new Promise(resolve => setTimeout(resolve, 15000));

        await browser.close();
        res.json({ success: response && response.status() === 200 });

    } catch (error) {
        console.error('Error generating report:', error);
        res.status(500).json({ success: false, message: 'Error generating report' });
    }
});


const port = 3000;
app.listen(port, () => {
    console.log(`Server running on http://localhost:${port}`);
});