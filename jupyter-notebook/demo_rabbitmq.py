
# coding: utf-8

# In[ ]:


# install mendatory packages
get_ipython().system('pip install pika')
get_ipython().system('pip install redis')


# In[2]:


import pika
import redis


# ### Play with Redis

# In[8]:


redis_cnx = redis.Redis( host='redis', port=6379, db=0 )


# In[9]:


redis_key1 = 'demo:key1'
value = 'hello world'
redis_cnx.set( redis_key1, value, ex=6000 )
value_from_cache = redis_cnx.get(redis_key1)
print(value_from_cache)


# ### Play with RabbitMQ

# In[11]:


# Send a message to rabbitmq

def rabbitmq_connect(host, port, username, password):
    credentials = pika.PlainCredentials(username, password)
    connection = pika.BlockingConnection(pika.ConnectionParameters(host, port, credentials=credentials))
    channel = connection.channel()
    return connection, channel

rabbitmq_cnx, rabbitmq_channel = rabbitmq_connect('rabbitmq', 5672, 'guest', 'guest')


# In[7]:


rabbitmq_channel.basic_publish(exchange='exchange1', routing_key='hello_topic', body='hello world from jupyter')


# In[ ]:


# send a single message
rabbitmq_channel.basic_publish(exchange='exchange1', routing_key='hello_topic', body='hello world from jupyter')


# In[ ]:


# send 100K messages
for i in range(100000):
    rabbitmq_channel.basic_publish(exchange='exchange1', routing_key='hello_topic', body='hello world from jupyter {}'.format(i))


# In[ ]:


rabbitmq_cnx.close()

