#ifndef TEST_TEE_CLIENT_API_H
#define TEST_TEE_CLIENT_API_H

#include <stddef.h>
#include <stdint.h>

typedef uint32_t TEEC_Result;
typedef struct {
	uint32_t timeLow;
	uint16_t timeMid;
	uint16_t timeHiAndVersion;
	uint8_t clockSeqAndNode[8];
} TEEC_UUID;
typedef struct { int unused; } TEEC_Context;
typedef struct { int unused; } TEEC_Session;

typedef struct {
	void *buffer;
	size_t size;
} TEEC_TempMemoryReference;

typedef struct {
	TEEC_TempMemoryReference tmpref;
} TEEC_Parameter;

typedef struct {
	uint32_t paramTypes;
	TEEC_Parameter params[4];
} TEEC_Operation;

#define TEEC_SUCCESS              0x00000000U
#define TEEC_ERROR_SHORT_BUFFER   0xFFFF0010U
#define TEEC_ERROR_OUT_OF_MEMORY  0xFFFF000CU
#define TEEC_ERROR_ITEM_NOT_FOUND 0xFFFF0008U
#define TEEC_ERROR_TARGET_DEAD    0xFFFF3024U
#define TEEC_ERROR_COMMUNICATION 0xFFFF000EU

#define TEEC_LOGIN_PUBLIC 0U
#define TEEC_NONE 0U
#define TEEC_MEMREF_TEMP_INPUT 1U
#define TEEC_MEMREF_TEMP_OUTPUT 2U
#define TEEC_PARAM_TYPES(t0, t1, t2, t3) \
	((uint32_t)(t0) | ((uint32_t)(t1) << 4) | \
	 ((uint32_t)(t2) << 8) | ((uint32_t)(t3) << 12))

TEEC_Result TEEC_InitializeContext(const char *name, TEEC_Context *ctx);
TEEC_Result TEEC_OpenSession(TEEC_Context *ctx, TEEC_Session *sess,
	const TEEC_UUID *uuid, uint32_t login, const void *connection,
	TEEC_Operation *operation, uint32_t *origin);
TEEC_Result TEEC_InvokeCommand(TEEC_Session *sess, uint32_t command,
	TEEC_Operation *operation, uint32_t *origin);
void TEEC_CloseSession(TEEC_Session *sess);
void TEEC_FinalizeContext(TEEC_Context *ctx);

#endif
