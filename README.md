# Parsing with derivatives
A Python implementation of parsing with derivatives. Provides a concise infix notation to support legible, complex grammars.

See http://maniagnosis.crsr.net/2012/04/parsing-with-derivatives-introduction.html for a Java implementation, or http://matt.might.net/articles/parsing-with-derivatives/ for the original author's publication.

## Example parser
![Example Parser Equation S = epsilon OR 1 AND S](https://latex.codecogs.com/png.latex?\dpi{150}&space;\huge&space;S&space;=&space;\epsilon&space;|&space;1&space;\cdot&space;S)
This parser would be represented as 
```python
S = Recurrence()
s.parser = epsilon | (1 & s)
```

This parser could parse any number of ones, before terminating.

A Python parser example can be found in python.py. It may not entirely be correct; small errors in the grammar may exist due to a hasty translation from the Python 3 official grammar.  