# -*- coding: utf-8 -*-
#!/usr/bin/env python


from typing import Any, Dict, List, Optional, Union
import math


def calculate_average(numbers: List):
    total = 0
    for number in numbers:
        total += number
    args_len = int(len(numbers))
    if args_len != 0:
        avg = total / int(len(numbers))
    else:
        avg = 0
    print(f"# Average: {avg}")
    return avg

def add_numbers(a, b):
    return a + b

def multiply_list(numbers):
    result = 1
    for num in numbers:
        result *= num
    return result

def sqrt(number):
    return math.sqrt(number)


class AdvancedMath:
    def power(self, base, exponent):
        return base ** exponent