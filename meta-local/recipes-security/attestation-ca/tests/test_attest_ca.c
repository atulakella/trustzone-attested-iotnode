#include <assert.h>
#include <stdio.h>
#include <string.h>
#include <sys/types.h>

#include "../files/attestation_ta.h"

static int evidence_mode;

#define main attest_ca_entry
#include "../files/attest_ca.c"
#undef main

ssize_t getrandom(void *buffer, size_t length, unsigned int flags)
{
	(void)buffer;
	(void)length;
	(void)flags;
	return -1;
}

TEEC_Result TEEC_InitializeContext(const char *name, TEEC_Context *ctx)
{
	(void)name;
	(void)ctx;
	return TEEC_SUCCESS;
}

TEEC_Result TEEC_OpenSession(TEEC_Context *ctx, TEEC_Session *sess,
	const TEEC_UUID *uuid, uint32_t login, const void *connection,
	TEEC_Operation *operation, uint32_t *origin)
{
	(void)ctx;
	(void)sess;
	(void)uuid;
	(void)login;
	(void)connection;
	(void)operation;
	if (origin)
		*origin = 0;
	return TEEC_SUCCESS;
}

TEEC_Result TEEC_InvokeCommand(TEEC_Session *sess, uint32_t command,
	TEEC_Operation *operation, uint32_t *origin)
{
	size_t len;

	(void)sess;
	(void)command;
	if (origin)
		*origin = 0;
	if (evidence_mode == 1) {
		operation->params[1].tmpref.size = ATT_OFF_SIG - 1;
		return TEEC_SUCCESS;
	}

	len = ATT_OFF_SIG + 3;
	memset(operation->params[1].tmpref.buffer, 0, len);
	((unsigned char *)operation->params[1].tmpref.buffer)[ATT_OFF_SIG_LEN] = 0;
	((unsigned char *)operation->params[1].tmpref.buffer)[ATT_OFF_SIG_LEN + 1] =
		(evidence_mode == 2) ? 2 : 3;
	operation->params[1].tmpref.size = len;
	return TEEC_SUCCESS;
}

void TEEC_CloseSession(TEEC_Session *sess)
{
	(void)sess;
}

void TEEC_FinalizeContext(TEEC_Context *ctx)
{
	(void)ctx;
}

static void test_parse_hex(void)
{
	uint8_t out[ATT_NONCE_LEN];

	assert(parse_hex("00000000000000000000000000000000"
			"00000000000000000000000000000000", out,
			sizeof(out)) == 0);
	assert(out[0] == 0x00 && out[15] == 0x00 && out[31] == 0x00);
	assert(parse_hex("00000000000000000000000000000000"
			"0000000000000000000000000000000", out,
			sizeof(out)) != 0);
	assert(parse_hex("00000000000000000000000000000000"
			"000000000000000000000000000000G0", out,
			sizeof(out)) != 0);
	assert(parse_hex("00000000000000000000000000000000"
			"0000000000000000000000000000000F", out,
			sizeof(out)) == 0);
}

static int run_client(int mode)
{
	char *argv[] = { (char *)"attest_ca",
		(char *)"00000000000000000000000000000000"
			"00000000000000000000000000000000", NULL };

	evidence_mode = mode;
	return attest_ca_entry(2, argv);
}

static void test_evidence_framing(void)
{
	assert(run_client(0) == 0);
	assert(run_client(1) == 3);
	assert(run_client(2) == 3);
}

int main(void)
{
	test_parse_hex();
	test_evidence_framing();
	puts("attestation client tests: passed");
	return 0;
}
