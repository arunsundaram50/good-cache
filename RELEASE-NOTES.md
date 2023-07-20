## 0.1.32
Added evict attribute-function to the decorated function to clear/evict cache

If your function was decorated like so:
```
  @fs_files_cache(files="filenames", args_to_str=my_args_to_str)
  def only_params_with_files_custom(filenames, a, b):
    print('processing a+b')
    return str(a+b)+str(filenames)
```

You would normally call, like so, and it will write the output to a cache file and use it 
during the next call with the same set of parameters (unless the files changed)
```
x = only_params_with_files_custom(['/tmp/a.txt', '/tmp/b.txt'], 1, 25)
print(x)
```

However, even if the files did not change, and you still want to remove the cache file so that
you force a call to the target function, you can call evict like so:
```
evicted = only_params_with_files_custom.evict(['/tmp/a.txt', '/tmp/b.txt'], 1, 25)
if not evicted:
  _, cache_file, _, _ = only_params_with_files_custom.get_cache_file`(['/tmp/a.txt', '/tmp/b.txt'], 1, 25)
  print(f'The {cache_file=} was not found to delete')
```
Not very surprisingly, the parameters to `only_param_with_files_custom` calls have be exact for `good_cache` for it to deal with the correct cached information.
