from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import time
from subprocess import call

def visit(url):
    try:
        call(['node', 'bot/bot.js', url])
        return True
    except:
        return False