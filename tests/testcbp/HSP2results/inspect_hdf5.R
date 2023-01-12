#!/usr/bin/R
library("rhdf5") #https://bioc.ism.ac.jp/packages/3.4/bioc/vignettes/rhdf5/inst/doc/rhdf5.pdf

# Find and load the h5 file
# dir()
# getwd()
setwd("C:/Users/nrf46657/Desktop/GitHub/HSPsquared/tests/testcbp/HSP2results")

# specify .h5 file
h5_file_name = "C:/Users/nrf46657/Desktop/GitHub/HSPsquared/tests/testcbp/HSP2results/PL3_5250_0001.h5"
content.df <- h5ls(h5_file_name,all=TRUE)
colnames(content.df)

# retrieve HYDR table
HYDR_table <- h5read(h5_file_name, "RESULTS/RCHRES_R001/HYDR/table")

# helpful printouts
# HYDR_table[1:10,]
# tail(HYDR_table)
# length(HYDR_table[,1])

# save HYDR table as csv
write.csv(HYDR_table, paste0("HYDR_table_",Sys.Date(),".csv"))
