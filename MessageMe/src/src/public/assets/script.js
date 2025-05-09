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