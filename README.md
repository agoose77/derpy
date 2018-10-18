# Parsing with derivatives
A Python implementation of parsing with derivatives. Provides a concise infix notation to support legible, complex grammars.

See http://maniagnosis.crsr.net/2012/04/parsing-with-derivatives-introduction.html for a Java implementation, or http://matt.might.net/articles/parsing-with-derivatives/ for the original author's publication.

## What is parsing?
According to Wikipedia, parsing is 
> the formal analysis by a computer of a sentence or other string of words into its constituents, resulting in a parse tree showing their syntactic relation to each other, which may also contain semantic and other information.

Typically, the process of producing a parse tree is separated into two distinct phases; lexing, and parsing.
Lexing simply breaks down a continuous stream of characters into course, discrete 'tokens'. Parsing then consumes these tokens to build the parse tree. 

This library provides both a simple tokeniser, and the parsing constructs required to build a parse tree from any given input and context free grammar.

## What can this library be used for?
There are several scenarios in which one might write a lexer/parser. Such scenarios include transpiling between languages, modifying source code (such as decorating all functions starting with the name "funky"), writing a DSL ...

## Example parser
![Parser syntax](https://latex.codecogs.com/png.latex?\dpi{150}&space;\large&space;s&space;=&space;\epsilon&space;|&space;1&space;\cdot&space;s)

This parser would be represented as 
```python
from derpy import rec, lit, empty_string
s = rec()
s.parser = empty_string | (lit('1') & s)
```

Or in short-hand
```python
s = rec()
s.parser = ~(lit('1') & s)
```

This parser could parse any number of ones, before terminating.
```python
from derpy import Token, parse

parse(s, [Token('1', 1) for i in range(5)])
>> {(1, (1, (1, (1, (1, '')))))}
```


## Python Grammar Parsing
A Python parser example can be found in the `derpy.grammars.python` module.
It may not entirely be correct; small errors in the grammar may exist due to a hasty translation from the Python 3 official grammar. Alternatively, the EBNF parser can be used to produce a Python grammar parser.

Most of the lines of code are devoted to outputting a useful AST (but for around 1200 loc, it's still quite compact). A custom `derpy.ast` module is defined to allow a similar API to the built-in ast module (In fact, the ast output was tested with an existing ast-to-code utility, simply by replacing the import to ast with our own).

## [Py]EBNF Grammar Meta Parsing
An example of parsing the Python EBNF grammar, to produce the source for a Python parser, can be found in the `derpy.grammars.ebnf`
To make this usable as an AST generator requires some formatting of each rule (using a reduction), which can be done by using custom reduction rules on the output of the generator. The produced Python grammar can be compared against the hand-rolled one in `python`
