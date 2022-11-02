
#### Redis

A channel layer is a kind of a communication system, which allows multiple parts of our application to exchange messages, without shuttling all the messages or events through the database.

We need a channel layer to give consumers the ability to talk to one another.

While we could use use the InMemoryChannelLayer layer since we're in development mode, we'll use a production-ready layer, RedisChannelLayer.

Since this layer requires Redis, run the following command to get it up and running with Docker:

(env)$ docker run -p 6379:6379 -d redis:5