### Compilation/Linking Tools and Flags ###

PYTHON = python
PYTHON_FLAGS = 

### Project Files and Directories ###

PROJ_DIR = .
BIN_DIR = $(PROJ_DIR)/bin
SRC_DIR = $(PROJ_DIR)/dmtg
OUT_DIR = $(PROJ_DIR)/out

PROJ_MAIN = $(PROJ_DIR)/dmtg.py

### Build Rules ###

.PHONY : main

all : main

main : $(PROJ_MAIN)
	$(PYTHON) $(PYTHON_FLAGS) $< rtr

tidy :
	rm -rf $(OUT_DIR)/base-in $(OUT_DIR)/base-out

clean :
	rm -rf $(SRC_DIR)/*.pyc $(OUT_DIR)
