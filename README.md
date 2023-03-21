# good-cache
Python based decorators to take the drudgery out of executing function only when needed

## What does it do?
Caches the output so that the decorated function, say f(), don't have to recompute a perhaphs CPU/GPU intensive, expensive. or a long-running computation.
And this is accomplised so that any existing calls to f(), or even f() itself, doesn't have to be modified. Only the decorator have to be applied to f().

## What is the use case?
You have a function f() that 
- (optionally) depends on a set of input files
- (optionally) depends on some input parameters
- the output of f() does not change if 
    - the input files haven't been modified since the last call to f() 
    - and/or the values of the input parameters haven't changeed

## What does the decorator do?
The decorator makes a copy of what f() produces and reuses it whenever possible. 

