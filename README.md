# OXBot

#### Just an simple IRC bot for personal usage.

The usage is very simple. Configure the file like **bot-params.json**
with your own preferences and run:

```python oxbot.py <configuration-file.json>```


#### Running commands
The syntax is simple:

```!bot-nick <command>```


#### Current implemented commands
###### Indiscriminate usage:

``` (HELP|PING|TIME) ```
>```HELP``` = Show available commands

>```PING``` = Return PONG

>```TIME``` = Show current time

###### De uso configurado:
###### Usage for configured users:
Only users previously set in **owners** parameter in configuration
file can run the following commands:

``` (BYE|RELOAD) ```
>```BYE``` = Shutdown bot

>```RELOAD``` = Reload the settings of bot (if the configuration file
was changed while bot online


Send your pull request. :)