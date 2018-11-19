# Tutorial Python Rabbitmq

Tutorial using python and rabbitmq.


## Useful links

https://www.cloudamqp.com/blog/2015-05-18-part1-rabbitmq-for-beginners-what-is-rabbitmq.html
https://www.cloudamqp.com/blog/2015-05-21-part2-3-rabbitmq-for-beginners_example-and-sample-code-python.html
https://www.cloudamqp.com/blog/2017-12-29-part1-rabbitmq-best-practice.html

https://www.rabbitmq.com/documentation.html
https://www.rabbitmq.com/cli.html

https://pika.readthedocs.io/en/stable/examples.html
https://pika.readthedocs.io/en/stable/examples/asynchronous_publisher_example.html
https://pika.readthedocs.io/en/stable/examples/asynchronous_consumer_example.html

https://www.rabbitmq.com/tutorials/tutorial-five-python.html
https://dev.to/usamaashraf/microservices--rabbitmq-on-docker-e2f



## Rabbitmq

Default login/password for gui is guest/guest

http://localhost:15672/


## Test webservice

    $ curl localhost:8182/ping
    $ curl -X POST http://127.0.0.1:8182/hello/nico

## Benchmark with siege

Note: this demo is not optimized for performance yet.
Flask is using werkzeug http server which is not optimal.

    $ siege -r 10 -c 50 --content-type="application/json" 'http://localhost:8182/hello/nico POST'

Results with create a rabbitmq cnx and release it for each message:

Transactions:                    500 hits
Availability:                 100.00 %
Elapsed time:                   9.66 secs
Data transferred:               0.01 MB
Response time:                  0.65 secs
Transaction rate:              51.76 trans/sec
Throughput:                     0.00 MB/sec
Concurrency:                   33.54
Successful transactions:         500
Failed transactions:               0
Longest transaction:            0.86
Shortest transaction:           0.04

Results with reusing an already opened rabbitmq cnx:

Transactions:                    500 hits
Availability:                 100.00 %
Elapsed time:                   4.11 secs
Data transferred:               0.01 MB
Response time:                  0.06 secs
Transaction rate:             121.65 trans/sec
Throughput:                     0.00 MB/sec
Concurrency:                    6.78
Successful transactions:         500
Failed transactions:               0
Longest transaction:            0.26
Shortest transaction:           0.00


## Docker stuff

    $ docker-compose up -d --no-deps --build pywebapi
    $ docker-compose up -d --no-deps swagger-ui


### Install portainer

    $ docker volume create portainer_data
    $ docker run -d -p 9000:9000 -v /var/run/docker.sock:/var/run/docker.sock -v portainer_data:/data --name portainer portainer/portainer


#### Portainer troubleshooting

If a message "Your session has expired" always appears when you try to log in with the portainer web interface then check your system date,
maybe you need to sync ntp because the date is not accurate.

    $ sudo yum install ntp -y
    $ systemctl enable ntpd
    $ systemctl start ntpd


## Troubleshoting

If container rabbitmq is not up and running then any client can't connect to the server.

Example with pyconsumer trying access rabbitmqserver:


```
pywebapi_1_d69b1e1dbd92 | [2018-11-16 13:40:10,000] INFO in main: configure rabbitmq
pywebapi_1_d69b1e1dbd92 | 2018-11-16 13:40:10,010 :: INFO :: Pika version 0.12.0 connecting to 172.18.0.2:5672
pywebapi_1_d69b1e1dbd92 | 2018-11-16 13:40:10,010 :: ERROR :: Connection to 172.18.0.2:5672 failed: [Errno 111] Connection refused
pywebapi_1_d69b1e1dbd92 | 2018-11-16 13:40:10,010 :: WARNING :: Could not connect, 0 attempts left
pywebapi_1_d69b1e1dbd92 | 2018-11-16 13:40:10,011 :: ERROR :: Connection open failed - 'Connection to 172.18.0.2:5672 failed: [Errno 111] Connection refused'
pywebapi_1_d69b1e1dbd92 | [2018-11-16 13:40:10,011] ERROR in main: exception rabbitmq config: Connection to 172.18.0.2:5672 failed: [Errno 111] Connection refused
pywebapi_1_d69b1e1dbd92 | Traceback (most recent call last):
pywebapi_1_d69b1e1dbd92 |   File "/app/src/main.py", line 138, in <module>
pywebapi_1_d69b1e1dbd92 |     rabbitmq_configure(settings['rabbitmq'])
pywebapi_1_d69b1e1dbd92 |   File "/app/src/main.py", line 46, in rabbitmq_configure
pywebapi_1_d69b1e1dbd92 |     connection, channel = rabbitmq_connect()
pywebapi_1_d69b1e1dbd92 |   File "/app/src/main.py", line 39, in rabbitmq_connect
pywebapi_1_d69b1e1dbd92 |     credentials=credentials))
pywebapi_1_d69b1e1dbd92 |   File "/usr/local/lib/python3.6/site-packages/pika/adapters/blocking_connection.py", line 377, in __init__
pywebapi_1_d69b1e1dbd92 |     self._process_io_for_connection_setup()
pywebapi_1_d69b1e1dbd92 |   File "/usr/local/lib/python3.6/site-packages/pika/adapters/blocking_connection.py", line 417, in _process_io_for_connection_setup
pywebapi_1_d69b1e1dbd92 |     self._open_error_result.is_ready)
pywebapi_1_d69b1e1dbd92 |   File "/usr/local/lib/python3.6/site-packages/pika/adapters/blocking_connection.py", line 471, in _flush_output
pywebapi_1_d69b1e1dbd92 |     raise exceptions.ConnectionClosed(maybe_exception)
pywebapi_1_d69b1e1dbd92 | pika.exceptions.ConnectionClosed: Connection to 172.18.0.2:5672 failed: [Errno 111] Connection refused
```






