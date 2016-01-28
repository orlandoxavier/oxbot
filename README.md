# OXBot


#### Um simples IRC bot para uso pessoal.

Para utilizar basta configurar o arquivo **bot-params.json** com
suas configurações personalizadas e executar:

```python oxbot.py <configuration-file.json>```


#### Usando
A sintáxe para executar comandos é simples:

```!nick-do-bot <<COMANDO>>```


#### Comandos implementados
###### De uso indiscriminado:

``` (HELP|PING|TIME) ```
>```HELP``` = Mostra os comandos disponíveis
>```PING``` = Retorna PONG
>```TIME``` = Diz a hora atual

###### De uso configurado:
Apenas usuários previamente definidos no parâmetro **'owners'** no 
arquivo de configuração poderão executar esses comandos.

``` (BYE|RELOAD) ```
>```BYE``` = Desliga o bot
>```RELOAD``` = Recarrega as configurações do bot (caso tenha alterado
o arquivo de configuração ou de respostas com o bot ligado) 

Manda seu pull request. :)