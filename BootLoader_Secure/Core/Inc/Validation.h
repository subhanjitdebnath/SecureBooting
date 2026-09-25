/*
 * Validation.h
 *
 *  Created on: Sep 20, 2026
 *      Author: Subhanjit Debnath
 */

#ifndef INC_VALIDATION_H_
#define INC_VALIDATION_H_
#include "main.h"

#define ROTRIGHT(a,b) (((a) >> (b)) | ((a) << (32-(b))))
#define CH(x,y,z) (((x) & (y)) ^ (~(x) & (z)))
#define MAJ(x,y,z) (((x) & (y)) ^ ((x) & (z)) ^ ((y) & (z)))
#define EP0(x) (ROTRIGHT(x,2) ^ ROTRIGHT(x,13) ^ ROTRIGHT(x,22))
#define EP1(x) (ROTRIGHT(x,6) ^ ROTRIGHT(x,11) ^ ROTRIGHT(x,25))
#define SIG0(x) (ROTRIGHT(x,7) ^ ROTRIGHT(x,18) ^ ((x) >> 3))
#define SIG1(x) (ROTRIGHT(x,17) ^ ROTRIGHT(x,19) ^ ((x) >> 10))

typedef struct {
    uint8_t data[64];
    uint32_t datalen;
    uint64_t bitlen;
    uint32_t state[8];
} SHA256_CTX;

static const uint32_t k[64] = {
		   0x428a2f98,0x71374491,0xb5c0fbcf,0xe9b5dba5,0x3956c25b,0x59f111f1,0x923f82a4,0xab1c5ed5,
		   0xd807aa98,0x12835b01,0x243185be,0x550c7dc3,0x72be5d74,0x80deb1fe,0x9bdc06a7,0xc19bf174,
		   0xe49b69c1,0xefbe4786,0x0fc19dc6,0x240ca1cc,0x2de92c6f,0x4a7484aa,0x5cb0a9dc,0x76f988da,
		   0x983e5152,0xa831c66d,0xb00327c8,0xbf597fc7,0xc6e00bf3,0xd5a79147,0x06ca6351,0x14292967,
		   0x27b70a85,0x2e1b2138,0x4d2c6dfc,0x53380d13,0x650a7354,0x766a0abb,0x81c2c92e,0x92722c85,
		   0xa2bfe8a1,0xa81a664b,0xc24b8b70,0xc76c51a3,0xd192e819,0xd6990624,0xf40e3585,0x106aa070,
		   0x19a4c116,0x1e376c08,0x2748774c,0x34b0bcb5,0x391c0cb3,0x4ed8aa4a,0x5b9cca4f,0x682e6ff3,
		   0x748f82ee,0x78a5636f,0x84c87814,0x8cc70208,0x90befffa,0xa4506ceb,0xbef9a3f7,0xc67178f2
		};

typedef enum _bool
{
	FALSE,
	TRUE
}Bool;

typedef enum _validationType
{
	SHA_256,
	DIGITAL_SIGNATURE,
	MAC_AUTHENTICATION
}ValidationType;


/* Complete Application Code validation Structure*/
#pragma pack(push, 1)
typedef struct _HashingData
{
	uint8_t			Validation;  			//1bytes
	uint32_t		Address;     			//4bytes
	uint32_t		Length;					//4bytes
	uint8_t		    sha[32];				//32bytes
}HashingData;
#pragma pack(pop)
typedef union _HeaderData
{
    HashingData			HashingData;		//1byte
    uint8_t		        Data[sizeof(HashingData)];				//32bytes
}HeaderData;

#define APP_HEADER				0x800ffd4
#define APP_ADDRESS				0x8010000

void Jump_to_RST(void);
void Read_App_Header(uint32_t* address);
Bool Validate_application(uint32_t address, uint32_t length);
void Jump_to_application(void);

void sha256_transform(SHA256_CTX *ctx, const uint8_t data[]);
void sha256_init(SHA256_CTX *ctx);
void sha256_update(SHA256_CTX *ctx, const uint8_t data[], size_t len);
void sha256_final(SHA256_CTX *ctx, uint8_t hash[]);
void compute_app_sha256(uint8_t *out_hash);

#endif /* INC_VALIDATION_H_ */
