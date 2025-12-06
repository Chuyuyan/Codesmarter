#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Test Chinese keyword detection in analysis_detector"""

from backend.modules.analysis_detector import detect_analysis_type

print("=== Testing Chinese Auto-Detection ===\n")

# Test Chinese questions
chinese_tests = [
    ("解释这段代码", "explain"),
    ("说明这个函数的作用", "explain"),
    ("修复这个bug", "debug"),
    ("这个错误怎么解决", "debug"),
    ("优化这段代码的性能", "optimize"),
    ("为什么这么慢", "optimize"),
    ("重构这个模块", "refactor"),
    ("改进代码质量", "refactor"),
    ("创建一个新项目", "generate"),
    ("生成一个全栈应用", "generate"),
]

print("Chinese Questions:")
for question, expected in chinese_tests:
    result = detect_analysis_type(question)
    status = "OK" if result == expected else "FAIL"
    print(f"{status} '{question}' -> {result} (expected: {expected})")

print("\n=== Testing English (for comparison) ===\n")

english_tests = [
    ("explain this code", "explain"),
    ("fix this bug", "debug"),
    ("optimize performance", "optimize"),
    ("refactor this module", "refactor"),
    ("create a new project", "generate"),
]

print("English Questions:")
for question, expected in english_tests:
    result = detect_analysis_type(question)
    status = "OK" if result == expected else "FAIL"
    print(f"{status} '{question}' -> {result} (expected: {expected})")

print("\n=== Test Complete ===")

