CC ?= cc
CFLAGS ?= -std=c11 -Wall -Wextra -Wshadow -Werror
CFLAGS += -Iinclude -I../files

test_attest_ca: test_attest_ca.c
	$(CC) $(CFLAGS) -o $@ $<

test: test_attest_ca
	./test_attest_ca

clean:
	rm -f test_attest_ca

.PHONY: test clean
