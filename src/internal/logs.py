#!/usr/bin/env python3
from colorama import Fore, Back, Style
import os

if "LOG_LEVEL" not in os.environ:
	os.environ["LOG_LEVEL"] = "info"

def DEBUG(where:str, *args, **kwargs):
	if os.environ["LOG_LEVEL"].lower() in ("debug"):
		print(Fore.MAGENTA, "[DEBUG]"+where, Style.RESET_ALL, *args, **kwargs)

def INFO(where:str, *args, **kwargs):
	if os.environ["LOG_LEVEL"].lower() in ("debug", "info"):
		print(Style.DIM, "[INFO]"+where, Style.RESET_ALL, *args, **kwargs)

def WARN(where:str, *args, **kwargs):
	if os.environ["LOG_LEVEL"].lower() in ("debug", "info", "warn"):
		print(Fore.YELLOW, "[WARN]"+where, Style.RESET_ALL, *args, **kwargs)	

def ERROR(where:str, *args, **kwargs):
	if os.environ["LOG_LEVEL"].lower() in ("debug", "info", "warn", "error"):
		print(Fore.RED, "[!ERROR!]"+where, Style.RESET_ALL, *args, **kwargs)
