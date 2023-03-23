# good-cache
Good-cache includes a collection of Python-based decorators that has the logic to decide whether to execute the decorated function or to use the cached values. This helps to keep the function clean as it avoids the drudgery of embedding the logic all over the place inside of the function.

## What does it do?
It caches the output so that the decorated function, say f(), don't have to recompute a perhaphs CPU/GPU intensive, cost-wise expensive, or a long-running computation.
Any existing calls to f(), or even f() itself, doesn't have to be modified. Only the decorator will have to be applied to f().

## What is the use case?
You have a function f() 
- that (optionally) depends on a set of input files. Some of it may be huge, and hence you want to avoid loading it whenever possible.
- that (optionally) depends on some input parameters
- whose output does not change if 
    - the input files haven't been modified since the last call to f() 
    - and/or the values of the input parameters haven't changeed

## What does the decorator do?
The decorator makes a copy of what f() produces and reuses it whenever possible. 
If reused, all things that f() did won't be done again.

## Here are examples:
### You have a file <code>stock-quotes.parquet</code> that looks so:
| ticker | date | price | 
|-|-|-|
|A|1999-01-01|15|
|AMZN|1999-01-01|24|
...



