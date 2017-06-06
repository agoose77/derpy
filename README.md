# Parsing with derivatives
A Python implementation of parsing with derivatives. Provides a concise infix notation to support legible, complex grammars.

See http://maniagnosis.crsr.net/2012/04/parsing-with-derivatives-introduction.html for a Java implementation, or http://matt.might.net/articles/parsing-with-derivatives/ for the original author's publication.

## Example parser
![Parser syntax](https://latex.codecogs.com/png.latex?\dpi{150}&space;\large&space;S&space;=&space;\epsilon&space;|&space;1&space;\cdot&space;S)

This parser would be represented as 
```python
from derp.parsers import Recurrence, lit, empty_string
s = Recurrence()
s.parser = empty_string | (lit('1') & s)
```

Or in short-hand
```python
s = Recurrence()
s.parser = ~(lit('1') & s)
```

This parser could parse any number of ones, before terminating.
```python
parse(s, [Token('1', 1) for i in range(5)])
>> {(1, (1, (1, (1, (1, '')))))}
```


## Operator notation
Operator overloading (+, >>, ~, &, |) makes the process of writing a grammar less verbose and simpler to read.

`P` represents a parser (e.g `s` in the above example)
* `+P` Regex *, 0 or more
* `~P` Optional
* `P >> f` Reduction (call f with result of parser)
* `|` Alternative (logical or)
* `&` Concatenate (logical and)

## Helpers
* `plus(P)` returns a tuple of 1+ matches of P
* `star(P)` functional name for `+P` (repeat)
* `opt(P)` functional name for `~P` (optional)
* `ter(c)` returns parser to match a token with the first attribute string equal to c.
* `seq(l, r)` returns Concatenation parser of left and right. 
* `alt(l, r)` returns Alternate parser of left and right. 

## Python Grammar Parsing
A Python parser example can be found in the `grammrs.python` module.
It may not entirely be correct; small errors in the grammar may exist due to a hasty translation from the Python 3 official grammar. Alternatively, the EBNF parser can be used to produce a Python grammar parser.

Most of the lines of code are devoted to outputting a useful AST (but for around 1200 loc, it's still quite compact). A custom `ast` module is defined to allow a similar API to the built-in ast module (In fact, the ast output was tested with an existing ast-to-code utility, simply by replacing the import to ast with our own).

## Funnel Grammar Parsing
A Funnel parser example can be found in the `grammars.funnel` module. Funnel is a custom lightweight language that allows embedded Python inside data model definitions

## [Py]EBNF Grammar Meta Parsing
An example of parsing the Python EBNF grammar, to produce the source for a Python parser, can be found in the `grammars.ebnf`
To make this usable as an AST generator requires some formatting of each rule (using a reduction), which can be done by using custom reduction rules on the output of the generator. The produced Python grammar can be compared against the hand-rolled one in `python`
