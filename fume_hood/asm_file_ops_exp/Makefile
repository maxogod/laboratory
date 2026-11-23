# Makefile for assembling and linking .S files

# Variables
SRCS := $(wildcard *.S)      # List of all .S files in the current directory
OBJS := $(patsubst %.S, %.o, $(SRCS))  # List of corresponding .o files
EXEC := my_program           # Executable name

# Compiler and linker options
AS := as                      # Assembler
ASFLAGS := -g                 # Assembler flags
LD := gcc                     # Linker
LDFLAGS := -no-pie -g         # Linker flags

# Targets
all: $(EXEC)

$(EXEC): $(OBJS)
	$(LD) $(LDFLAGS) $^ -o $@

%.o: %.S
	$(AS) $(ASFLAGS) $< -o $@

clean:
	rm -f $(OBJS) $(EXEC) test_struct.save

.PHONY: all clean

