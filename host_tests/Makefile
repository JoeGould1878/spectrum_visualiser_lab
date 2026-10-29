# Laptop tests for the pure-C components (no ESP32 needed).
#   make          build and run every test
#   make clean
# Each test_<name>.c is linked with components/<name>/<name>.c

CC      ?= gcc
CFLAGS  ?= -std=c11 -Wall -Wextra -Werror -g -O0
LDLIBS  := -lm
COMP    := ../components
BUILD   := build

TESTS   := band_map bar_model tone_finder frame_gfx

.PHONY: all run clean
all: run

$(BUILD):
	mkdir -p $(BUILD)

# $$* (second expansion) = the component name, used twice in each path
.SECONDEXPANSION:
$(BUILD)/test_%: test_%.c $$(COMP)/$$*/$$*.c $$(COMP)/$$*/include/$$*.h | $(BUILD)
	$(CC) $(CFLAGS) -I$(COMP)/$*/include test_$*.c $(COMP)/$*/$*.c -o $@ $(LDLIBS)

run: $(addprefix $(BUILD)/test_,$(TESTS))
	@for t in $^; do echo "== $$t"; ./$$t || exit 1; done
	@echo "All host tests passed."

clean:
	rm -rf $(BUILD)
