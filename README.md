# Parsing with derivatives
A Python implementation of parsing with derivatives. Provides a concise infix notation to support legible, complex grammars.

See http://maniagnosis.crsr.net/2012/04/parsing-with-derivatives-introduction.html for a Java implementation, or http://matt.might.net/articles/parsing-with-derivatives/ for the original author's publication.

## Example parser
```latex 
S = \epsilon | 1 \cdot  S
```
This parser would be represented as 
```python
S = Recurrence()
s.parser = epsilon | (1 & s)
```

This parser could parse any number of ones, before terminating.

A Python parser example can be found in python.py. It may not entirely be correct; small errors in the grammar may exist due to a hasty translation from the Python 3 official grammar.
Infix notation (+, >>, ~, &, |) is defined on each parser to make the process of writing a grammar less verbose and simpler to read.

## Infix notation
P represents a parser (e.g S above)
* `+P` Regex *, 0 or more
* `~P` Optional
* `P >> f` Reduction (call f with result of parser)
* `|` Or (alternative)
* `&` And (concat / sequence)

## Helpers
* `one_of(P)` returns a tuple of 1+ matches of P
* `greedy(P)` functional name for `+P` (repeat)
* `optional(P)` functional name for `~P` (optional)
* `ter(c)` returns parser to match a token with the `first` attribute string equal to c.
* `to_text(P, max_depth=None)` returns text representation of parser. Optionally limited to depth N