#!/usr/bin/env Rscript

library(stringr)

# functions
# ---------

#' load a dataframe and do some light reformatting
#' 
#' @param dir input directory
#' @param name name of file
#' @return loaded dataframe
load_and_format <- function(dir, name) {
  path <- paste(c(dir, name), collapse="/")
  table <- read.csv(path, header=TRUE, row.names='X', as.is=TRUE)
  colnames(table) <- gsub('X', '', colnames(table))
  return(table)
}

#' split the style from the base name of a font
#' 
#' @param name file name
#' @return base name and style of a font
get_style <- function(name) {
  cut_at <- str_locate(name, "[:punct:]")[1]
  if (is.na(cut_at)) {
    name <- gsub(".csv", "", name)
    return(list(base=name, style=""))
  }
  split <- str_split(name, "")[[1]]
  base <- str_flatten(head(split, n=cut_at-1))
  style <- str_flatten(tail(split, n=length(split) - cut_at))
  style <- gsub(".csv", "", style)
  return(list(base=base, style=style))
}

#' create metadata about the oc-occurrence table
#' 
#' @param df a font co-occurrence table, where 1 is a char:glyph mapping
#' @param name the name of the font
#' @return metadata row
make_record <- function(df, name) {
  style_info <- get_style(name)
  # if the dataframe is empty:
  if ((ncol(df) == 1) & (nrow(df) == 1)) {
    if (is.na(df[1, 1])) {
      n_dec <- 0
      n_homoglyphs <- 0
    }
  } else {
    n_dec <- ncol(df)
    n_homoglyphs <- nrow(df[rowSums(df) > 1, ])
  }
  record <- data.frame(
    NAME=name,
    BASE=style_info$base,
    STYLE=style_info$style,
    N_DEC=n_dec,
    N_HOMOGLYPHS=n_homoglyphs
  )
  return(record)
}

#' add the values of a new co-occurrence table to an existing one, taking into 
#' account row and column discrepancies, making new ones where appropriate
#' 
#' @param df_list the tables to add together
#' @return a new co-occurrence table that reflects the summed values of the tables
add_df <- function(df_list) {
  # get all unique rows and columns from the combined list of dataframes
  rows <- unique(unlist(lapply(df_list, rownames)))
  cols <- unique(unlist(lapply(df_list, colnames)))
  # make an empty matrix with those rows and columns
  mat <- matrix(
    NA,
    nrow=length(rows),
    ncol=length(cols),
    dimnames=list(rows, cols)
  )
  # for each dataframe in the list, find the associated rows and columns in the 
  # matrix. for un-associated rows and columns, fill with 0. add the dataframe 
  # to the rest
  for (i in seq_along(df_list)) {
    sub_rows <- rownames(df_list[[i]])
    sub_cols <- colnames(df_list[[i]])
    mat[sub_rows, sub_cols][is.na(mat[sub_rows, sub_cols])] <- 0
    mat[sub_rows, sub_cols] <- mat[sub_rows, sub_cols] + as.matrix(df_list[[i]])
  }
  return(as.data.frame(mat))
}

# command args and function calls
# -------------------------------

args <- commandArgs(trailingOnly=TRUE)
indir <- args[1]
outdir <- args[2]

files <- list.files(indir)
cat(paste(length(files), "files to merge"))

cat("\nMerging files")
count <- 0
meta <- data.frame()
coocc <- data.frame()
for (name in files) {
  cat(paste("\nLoading", name))
  df <- load_and_format(indir, name)
  record <- make_record(df, name)
  meta <- rbind(meta, record)
  df_list <- list(coocc, df)
  coocc <- add_df(df_list)
  rm(df, df_list)
  gc()
  count <- count + 1
  if (count %% 10 == 0) {
    cat(paste("\n+", count, "files merged"))
  }
}

coocc[is.na(coocc)] <- 0

outpath_meta <- paste(c(outdir, "metadata.csv"), collapse="/")
outpath_coocc <- paste(c(outdir, "cooc.csv"), collapse="/")
write.csv(meta, outpath_meta)
write.csv(coocc, outpath_coocc)
