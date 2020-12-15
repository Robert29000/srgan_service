# Инструкции по установке

![Alt text](/structure.jpg)

Для начала работы на сервере должно быть установлены *python* версии 3 и пакетный менеджер *pip*.
В качестве веб-сервера будем использовать *nginx*. Для установки необходимых пакетов пропишем следующую команду:

```sh
$ sudo apt install python3-pip python3-dev sqlite3 nginx curl gunicorn
```

После установки и обновления всех необходимых компонент, начнем настройку проекта. Для этого в папке проекта создадим и активируем виртуальную среду:

```sh
$ sudo apt install python3-venv
$ python -m venv ./venv
$ source venv/bin/activate
```

Далее необходимо установить нужные зависимости и создать папку для логов:

```sh
$ pip install -r requirements.txt
$ mkdir logs
```

Дальше необходимо сконфигурировать проект в *production*. Для этого изменяем в *srgan_service/settings.py* 
значение **DEBUG** на *False*. Также необходимо сгенерировать секретный ключ и записать его в переменную окружения *SECRET_KEY*:

```sh
$ export SECRET_KEY='Сгенерированное значение'
```

Для корректной работы в этом же файле в переменную *ALLOWED_HOSTS* пропишите ip-адресс сервера и домен, если есть. 
После этих шагов сервис готов к эксплуатации. Запускаем его использовав, следующие команды:

```sh
$ python manage.py makemigrations
$ python manage.py migrate 
```

По желанию можно создать пользователя с правами администратора и сделать настройку статических файлов:

```sh
$ python manage.py createsuperuser
$ python manage.py collectstatic
```

Дальше можем приступить к настройке *gunicorn* и *nginx*. Для начала выйдем из виртуальной среды:

```sh
$ deactivate
```

Изменим файл настройки gunicorn-сокета и пропишим следующее:

```sh
$ sudo nano /etc/systemd/system/gunicorn.socket
```

Пропишем:

```sh
[Unit]
Description=gunicorn socket

[Socket]
ListenStream=/run/gunicorn.sock

[Install]
WantedBy=sockets.target
```

Сохраним данный файл, и теперь сконфигурируем файл gunicorn-сервиса:

```sh
$ sudo nano /etc/systemd/system/gunicorn.service
```

Пропишем:

```sh
[Unit]
Description=gunicorn daemon
Requires=gunicorn.socket
After=network.target

[Service]
User=Имя пользователя
Group=Группа пользователя
WorkingDirectory=/Путь к /папке /проекта/srgan_service
ExecStart=/Путь к /папке /проекта/srgan_service/venv/bin/gunicorn --access-logfile - --workers 3 --bind unix:/run/gunicorn.sock srgan_service.wsgi:application

[Install]
WantedBy=multi-user.target
```

После этого сохраняем файл и запускаем *gunicorn*:

```sh
$ sudo systemctl start gunicorn.socket
$ sudo systemctl enable gunicorn.socket
```

Проверьте статус сервиса и наличие sock-файла:

```sh
$ sudo systemctl status gunicorn.socket
$ file /run/gunicorn.sock
```
Если файла нет или сервис не активен, значит нужно проверить файлы конфигирации. После успешной настройки *gunicorn* приступим к настройке *nginx*:

```sh
$ sudo nano /etc/nginx/sites-available/srgan_service
```

Пропишем:

```sh
server {
    server_name IP-Адресс Домен www.Домен

    location = /favicon.ico { access_log off; log_not_found off; }
    location /static/ {
        root /Путь к /папке /проекта/srgan_service;
    }
    
    location /media/ {
        root /Путь к /папке /проекта/srgan_service;    
    }

    location / {
        include proxy_params;
	    proxy_http_version 1.1; 
        proxy_temp_file_write_size 64k;
        proxy_connect_timeout 300s;
        proxy_send_timeout 300s;
        proxy_read_timeout 300s;
        proxy_buffer_size 64k;
        proxy_buffers 16 32k;
        proxy_busy_buffers_size 64k;
        proxy_redirect off;
        proxy_request_buffering off;
	    proxy_buffering off;
        proxy_pass http://unix:/run/gunicorn.sock;
    }

}
```

После сохранения файла конфигурации, привяжем данный файл к папке активных проектов *nginx*:

```sh
$ sudo ln -s /etc/nginx/sites-available/srgan_service /etc/nginx/sites-enabled
```

Протестируем *nginx*:

```sh
$ sudo nginx -t
```

Если тестирование прошло успешно, то перезапустим *nginx*:

```sh
$ sudo systemctl restart nginx
```

Для работы с изображениями возможно нужно будет увеличить допустимый размер тела запроса, для этого откроем файл *nginx.conf*:

```sh
$ sudo nano /etc/nginx/nginx.conf
$ client_max_body_size 20M; # Прописываем(или изменяем) эту строчку в блоке http
```

Если нужно добавить поддержку *https* для создания сертификата можно воспользоватся бесплатным сервисом **Certbot** от **Let's Encrypt**.
Установим данную утилиту и запустим процесс выдачи сертификата:

```sh
$ sudo apt install certbot python-certbot-nginx
$ sudo certbot –nginx
```

После этого следуем указаниям на экране. Так как сертификат выдается на 90 дней, пропишем автоматическое обновление сертификата:

```sh
$ sudo certbot renew --dry-run 
``` 

Теперь можно еще раз перезапустить *nginx* и *gunicorn* и проверить работу сервиса.
