File Map
--------

```
!compile_coocc.R/py     Adding together character co-occurrence tables*
combine_pairs.sh        Concatenate adjacency tables in a directory and sum duplicates
get_ttf_range.py        Use `fc-query` to find character ranges of `ttf` files
!stack_add.py           Create adjacency tables from co-occurrences; _attempt_ to sum duplicates*
```

`!`: deprecated

\* Note: these are likely to throw out-of-core problems; reduce the square matrices to adjacency
tables.
