# nginxkit

从字典格式的数据中生成nginx配置文件，理论上可以完全自定义任何nginx允许的合法配置

## 注意事项

- 传入的数据必须是字典格式
- 自定义关键字排序时，使用`sort_list`传入即可
- 处理 if、for 函数表达式的逻辑可能存在以下问题
  - 缩进格式错位
  - 缺少`\n`换行符时，无法正确被解析从而导致程序崩溃

## 示例

> Tips
> 若需要从环境变量获取值并处理，可以与[settingkit](https://github.com/YaKazama/settingkit.git)一起配合使用。
>

```python
import nginxkit

ngx = nginxkit.NginxBuilder(nginxkit.NGX_CONF_NGINX)

# 直接打印输出
print ngx.as_string()
# 写入文件
ngx.to_file()
```

## 致谢

- [朴文学](https://github.com/piao100101)
- [Fatih Erikli](https://github.com/fatiherikli)及其[nginxparser项目](https://github.com/fatiherikli/nginxparser)

