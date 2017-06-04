# Parsing with derivatives
A Python implementation of parsing with derivatives. Provides a concise infix notation to support legible, complex grammars.

See http://maniagnosis.crsr.net/2012/04/parsing-with-derivatives-introduction.html for a Java implementation, or http://matt.might.net/articles/parsing-with-derivatives/ for the original author's publication.

## Example parser
![Parser syntax](https://latex.codecogs.com/png.latex?\dpi{150}&space;\large&space;S&space;=&space;\epsilon&space;|&space;1&space;\cdot&space;S)

This parser would be represented as 
```python
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

P represents a parser (e.g S above)
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
A Python parser example can be found in the python module. It may not entirely be correct; small errors in the grammar may exist due to a hasty translation from the Python 3 official grammar.

Most of the lines of code are devoted to outputting a useful AST (but for around 1200 loc, it's still quite compact). A custom `ast` module is defined to allow a similar API to the built-in ast module (In fact, the ast output was tested with an existing ast-to-code utility, simply by replacing the import to ast with our own).

## Funnel Grammar Parsing
A Funnel parser example can be found in the funnel module. Funnel is a custom lightweight language that allows embedded Python inside data model definitions

## PyBNF Grammar Meta Parsing
An example of parsing a Python BNF-like grammar, to output a parser is given. Note, this is quite slow at parsing a full grammar, so it's more of a POC at this point.
