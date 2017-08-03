"""Parsing with derivatives
A Python implementation of parsing with derivatives. Provides a concise infix notation to support legible, complex grammars.

See http://maniagnosis.crsr.net/2012/04/parsing-with-derivatives-introduction.html for a Java implementation, or http://matt.might.net/articles/parsing-with-derivatives/ for the original author's publication.
"""
from . import ast
from .parsers import lit, cat, alt, opt, star, plus, parse, rec, red, empty_string, empty_parser
from .token import Token
from .tokenizer import Tokenizer
from .grammar import Grammar
from .utilities import unpack_n, rflatten