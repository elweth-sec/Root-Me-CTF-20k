const { app, BrowserWindow, ipcMain } = require('electron');
const path = require('path');
const axios = require('axios');
const cheerio = require('cheerio');

function createWindow(pseudo = null) {
    const win = new BrowserWindow({
        width: 800,
        height: 600,
        webPreferences: {
            nodeIntegration: true,
            contextIsolation: false,
        },
        icon: path.join(__dirname, 'assets', 'image.png')
    });

    win.loadURL(`file://${__dirname}/views/index.html`).then(() => {
        if (pseudo) {
            win.webContents.send('auto-get-user-info', pseudo);
        }
    });
}

app.on('ready', () => {
    const pseudo = process.argv[1];
    createWindow(pseudo);
});

ipcMain.handle('get-user-info', async (event, pseudo) => {
    console.log('Received get-user-info event, pseudo:', pseudo);
    try {
        const url = `https://www.root-me.org/${pseudo}?var_mode=calcul`;
        console.log(url)
        const response = await axios.get(url);
        const $ = cheerio.load(response.data);

        const imgSrc = $('img.vmiddle.logo_auteur.logo_5pre, img.vmiddle.logo_auteur.logo_6forum').attr('src');
        console.log('Extracted imgSrc:', imgSrc);

        const bioElement = $('li[class^="crayon auteur-bio-"]');
        const bio = bioElement.text() || '';
        console.log('Extracted bio:', bio);

        const html = response.data;

        const placeMatch = html.match(/<h3><img[^>]*>\s*&nbsp;(\d+)<\/h3>\s*<span class="gras">Place<\/span>/);
        const pointsMatch = html.match(/<h3><img[^>]*>\s*&nbsp;(\d+)<\/h3>\s*<span class="gras">Points<\/span>/);
        const challengesMatch = html.match(/<h3><img[^>]*>\s*&nbsp;(\d+)<\/h3>\s*<span class="gras">Challenges<\/span>/);
        const compromissionsMatch = html.match(/<h3><img[^>]*>\s*&nbsp;(\d+)<\/h3>\s*<span class="gras">Compromissions<\/span>/);

        const rank = placeMatch ? placeMatch[1] : 'N/A';
        const points = pointsMatch ? pointsMatch[1] : 'N/A';
        const challenges = challengesMatch ? challengesMatch[1] : 'N/A';
        const compromissions = compromissionsMatch ? compromissionsMatch[1] : 'N/A';

        console.log('Extracted rank:', rank);
        console.log('Extracted points:', points);
        console.log('Extracted challenges:', challenges);
        console.log('Extracted compromissions:', compromissions);

        const fullImgUrl = imgSrc ? `https://www.root-me.org/${imgSrc}` : null;

        return { image: fullImgUrl, bio: bio || null, rank, points, challenges, compromissions };
    } catch (error) {
        console.error('Error fetching user info:', error);
        return { image: null, bio: null, rank: 'N/A', points: 'N/A', challenges: 'N/A', compromissions: 'N/A' };
    }
});

app.on('window-all-closed', () => {
    if (process.platform !== 'darwin') {
        app.quit();
    }
});

app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
        createWindow();
    }
});
