# -*- coding: utf-8 -*-
""""""

from collections import OrderedDict
from sys import version_info as _pyv


NGX_CONF_NGINX = {
    'main': {
        'user': 'nginx',
        'worker_processes': 'auto',
        'pid': '/run/nginx.pid',
        'error_log': '/dev/stderr warn',
        'worker_rlimit_nofile': '65535',
        'include': ['/etc/nginx/modules-enabled/*.conf']
    },
    'events': {
        'worker_connections': '65535',
        'multi_accept': 'on',
        'use': 'epoll'
    },
    'http': {
        'log_format': [
            """main '$remote_addr - $remote_user [$time_local] "$request" '
                    '$status $body_bytes_sent "$http_referer" '
                    '"$http_user_agent" "$http_x_forwarded_for"'"""
        ],
        'access_log': '/dev/stdout main',
        'sendfile': 'on',
        'tcp_nopush': 'on',
        'tcp_nodelay': 'on',
        'keepalive_timeout': '3600',
        'types_hash_max_size': '2048',
        'keepalive_disable': 'none',
        'keepalive_requests': '5000',
        'client_max_body_size': '1024m',
        'include': ['/etc/nginx/mime.types', '/etc/nginx/conf.d/*.conf'],
        'default_type': 'application/octet-stream',
        'gzip': 'on',
        'gzip_vary': 'on',
        'gzip_buffers': '16 8k',
        'gzip_comp_level': '6',
        'gzip_disable': '"MSIE [1-6]\\."',
        'gzip_http_version': '1.1',
        'gzip_min_length': '32k',
        'gzip_proxied': 'off',
        'gzip_types': 'text/plain '
                        'text/css '
                        'application/json '
                        'application/javascript '
                        'text/xml '
                        'application/xml '
                        'application/xml+rss '
                        'text/javascript',
    }
}

NGX_CONF_NGINX_SIMPLE = {
    'user': 'nginx',
    'worker_processes': '4',
    'worker_rlimit_nofile': '65535',
    'pid': '/run/nginx.pid',
    'events': {
        'worker_connections': '65535',
        'multi_accept': 'on',
        'use': 'epoll'
    },
    'http': {
        'default_type': 'application/octet-stream',
        'more_clear_headers': "'Date' 'ETag' 'Last-Modified' 'Proxy-Connection' 'Server'",
        'include': [
            '/etc/nginx/mime.types',
            '/etc/nginx/conf.d/*.conf'
        ]
    }
}


class NginxBuilder(object):
    def __init__(self, obj, parrent='', indent=4, sort_list=[]):
        """
        一、使用字典格式传值

        完整数据结构，参考：nginx_settings.NGX_DEFAULT_CONFIG
        使用默认的log_format，参考：nginx_settings.NGX_DEFAULT_HTTP_LOG_FORMAT

        P.S.：在 location、upstream中，允许使用`ngx_<location|upstream>_<key_name>`
        注明location或upstream后的uri或name；其他配置若需要使用，需要确保前缀
        `ngx_<父级key>_*`可用。示例如下。

        ```bash
        {
            'upstream': {
                'ngx_upstream_name': 'default_upstream',
                'server': [
                    '127.0.0.1:9001 fail_timeout=5s max_fails=3',
                ]
            },
            'location': [
                {
                    'ngx_location_uri': '/',
                    'try_files': '$uri $uri/ =404',
                }
            ]
        }
        ```
        """
        self.obj = obj
        self.parrent = parrent
        self.indent = indent
        self.is_v2 = True if _pyv[:3] < (3, 6, 0) else False
        # 处理特殊关键字的顺序
        self.ss = sort_list if sort_list else [
            'load_module', 'include', 'log_format', 'access_log', 'events',
            'server', 'resolver', 'set', 'location', 'allow', 'deny',
            'rewrite', 'return'
        ]

    def __iter__(self, obj=None, parrent='', indent=0, spacer=' '):
        obj = obj if obj else self.obj
        parrent = parrent if parrent else self.parrent
        indentation = spacer * indent

        if isinstance(obj, dict):
            uri = 'uri'
            for _k in obj.iterkeys():
                key_prefix = 'ngx_{}_'.format(parrent)
                if _k.startswith(key_prefix):
                    uri = _k.split(key_prefix)[-1]

            # 打印 module：http、server、location、events
            ngx_key = 'ngx_{}_{}'.format(parrent, uri)
            uri_v = obj.pop(ngx_key, '')
            if uri_v:
                yield '\n{}{} {} {}'.format(indentation, parrent, uri_v, '{')
            elif parrent:
                yield '\n{}{} {}'.format(indentation, parrent, '{')

            # 处理特殊排序，转换为有序字典（3.6之后默认为有序字典）
            if self.is_v2:
                _obj = OrderedDict()

                l_in = []
                l_out = []
                obj_keys = sorted(obj.keys(), key=lambda item: item[1])
                for x in obj_keys:
                    if x not in self.ss:
                        l_in.append(x)
                        continue
                    l_out.append(x)
                obj_keys_new = l_in + sorted(l_out, key=self.ss.index)
                for k in obj_keys_new:
                    _obj[k] = obj[k]
                obj = _obj

            for key, value in obj.iteritems():
                key = '' if key == 'main' else key
                indent = -self.indent if key == 'main' or not parrent else indent
                res = self.__iter__(value, key, indent + self.indent)
                for line in res:
                    yield line

            if parrent:
                yield indentation + '}'
        elif isinstance(obj, (tuple, list)):
            for value in obj:
                res = self.__iter__(value, parrent, indent)
                for line in res:
                    yield line
        else:
            m = '{}{} {}'.format(indentation, parrent, obj)
            if not (m.endswith(';') or m.endswith('}')):
                m += ';'

            # 处理 if、for 函数表达式
            if parrent in ['if', 'for']:
                __lines = []
                if '\n' in m:
                    _lines = m.split('\n')
                    __lines.append(_lines[0])
                    res = self.__iter__(_lines[1:], '', indent - 1)
                    for x in res:
                        if '}' not in x:
                            x = '{}{}'.format(spacer * self.indent, x)
                        __lines.append(x)
                    m = '\n'.join(__lines)

            yield m

    def as_string(self):
        return '\n'.join(self)

    def to_string(self):
        return self.as_string()

    def to_file(self, out='nginx_default.conf'):
        with open(out, 'wb') as fp:
            for line in self:
                fp.write(line + '\n')
        return out


def default_nginx(out='nginx.conf', to_file=False):
    ngx = NginxBuilder(NGX_CONF_NGINX)
    if to_file:
        ngx.to_file(out)
    else:
        print(ngx.as_string())


def default_nginx_simple(out='nginx.conf', to_file=False):
    ngx = NginxBuilder(NGX_CONF_NGINX_SIMPLE)
    if to_file:
        ngx.to_file(out)
    else:
        print(ngx.as_string())


__all__ = []

