#!/opt/homebrew/bin/python3
from random import randint


var = 
startport = 8080
endport = 9090
portrange = (endport - startport)

randomport = randint(startport, endport)
print(randomport)