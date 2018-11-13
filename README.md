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

