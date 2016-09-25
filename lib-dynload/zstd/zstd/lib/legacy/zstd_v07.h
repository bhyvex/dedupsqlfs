/**
 * Copyright (c) 2016-present, Yann Collet, Facebook, Inc.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree. An additional grant
 * of patent rights can be found in the PATENTS file in the same directory.
 */

#ifndef ZSTDv07_H_235446
#define ZSTDv07_H_235446

#if defined (__cplusplus)
extern "C" {
#endif

/*======  Dependency  ======*/
#include <stddef.h>   /* size_t */


/*======  Export for Windows  ======*/
/*!
*  ZSTDv07_DLL_EXPORT :
*  Enable exporting of functions when building a Windows DLL
*/
#if defined(_WIN32) && defined(ZSTDv07_DLL_EXPORT) && (ZSTDv07_DLL_EXPORT==1)
#  define ZSTDLIB_API __declspec(dllexport)
#else
#  define ZSTDLIB_API
#endif



/* *************************************
*  Simple API
***************************************/
/*! ZSTDv07_getDecompressedSize() :
*   @return : decompressed size if known, 0 otherwise.
       note 1 : if `0`, follow up with ZSTDv07_getFrameParams() to know precise failure cause.
       note 2 : decompressed size could be wrong or intentionally modified !
                always ensure results fit within application's authorized limits */
unsigned long long ZSTDv07_getDecompressedSize(const void* src, size_t srcSize);

/*! ZSTDv07_decompress() :
    `compressedSize` : must be _exact_ size of compressed input, otherwise decompression will fail.
    `dstCapacity` must be equal or larger than originalSize.
    @return : the number of bytes decompressed into `dst` (<= `dstCapacity`),
              or an errorCode if it fails (which can be tested using ZSTDv07_isError()) */
ZSTDLIB_API size_t ZSTDv07_decompress( void* dst, size_t dstCapacity,
                              const void* src, size_t compressedSize);

/*======  Helper functions  ======*/
ZSTDLIB_API unsigned    ZSTDv07_isError(size_t code);          /*!< tells if a `size_t` function result is an error code */
ZSTDLIB_API const char* ZSTDv07_getErrorName(size_t code);     /*!< provides readable string from an error code */


/*-*************************************
*  Explicit memory management
***************************************/
/** Decompression context */
typedef struct ZSTDv07_DCtx_s ZSTDv07_DCtx;
ZSTDLIB_API ZSTDv07_DCtx* ZSTDv07_createDCtx(void);
ZSTDLIB_API size_t     ZSTDv07_freeDCtx(ZSTDv07_DCtx* dctx);      /*!< @return : errorCode */

/** ZSTDv07_decompressDCtx() :
*   Same as ZSTDv07_decompress(), requires an allocated ZSTDv07_DCtx (see ZSTDv07_createDCtx()) */
ZSTDLIB_API size_t ZSTDv07_decompressDCtx(ZSTDv07_DCtx* ctx, void* dst, size_t dstCapacity, const void* src, size_t srcSize);


/*-************************
*  Simple dictionary API
***************************/
/*! ZSTDv07_decompress_usingDict() :
*   Decompression using a pre-defined Dictionary content (see dictBuilder).
*   Dictionary must be identical to the one used during compression.
*   Note : This function load the dictionary, resulting in a significant startup time */
ZSTDLIB_API size_t ZSTDv07_decompress_usingDict(ZSTDv07_DCtx* dctx,
                                             void* dst, size_t dstCapacity,
                                       const void* src, size_t srcSize,
                                       const void* dict,size_t dictSize);


/*-**************************
*  Advanced Dictionary API
****************************/
/*! ZSTDv07_createDDict() :
*   Create a digested dictionary, ready to start decompression operation without startup delay.
*   `dict` can be released after creation */
typedef struct ZSTDv07_DDict_s ZSTDv07_DDict;
ZSTDLIB_API ZSTDv07_DDict* ZSTDv07_createDDict(const void* dict, size_t dictSize);
ZSTDLIB_API size_t      ZSTDv07_freeDDict(ZSTDv07_DDict* ddict);

/*! ZSTDv07_decompress_usingDDict() :
*   Decompression using a pre-digested Dictionary
*   Faster startup than ZSTDv07_decompress_usingDict(), recommended when same dictionary is used multiple times. */
ZSTDLIB_API size_t ZSTDv07_decompress_usingDDict(ZSTDv07_DCtx* dctx,
                                              void* dst, size_t dstCapacity,
                                        const void* src, size_t srcSize,
                                        const ZSTDv07_DDict* ddict);

typedef struct {
    unsigned long long frameContentSize;
    unsigned windowSize;
    unsigned dictID;
    unsigned checksumFlag;
} ZSTDv07_frameParams;

ZSTDLIB_API size_t ZSTDv07_getFrameParams(ZSTDv07_frameParams* fparamsPtr, const void* src, size_t srcSize);   /**< doesn't consume input */




/* *************************************
*  Streaming functions
***************************************/
typedef struct ZBUFFv07_DCtx_s ZBUFFv07_DCtx;
ZSTDLIB_API ZBUFFv07_DCtx* ZBUFFv07_createDCtx(void);
ZSTDLIB_API size_t      ZBUFFv07_freeDCtx(ZBUFFv07_DCtx* dctx);

ZSTDLIB_API size_t ZBUFFv07_decompressInit(ZBUFFv07_DCtx* dctx);
ZSTDLIB_API size_t ZBUFFv07_decompressInitDictionary(ZBUFFv07_DCtx* dctx, const void* dict, size_t dictSize);

ZSTDLIB_API size_t ZBUFFv07_decompressContinue(ZBUFFv07_DCtx* dctx,
                                            void* dst, size_t* dstCapacityPtr,
                                      const void* src, size_t* srcSizePtr);

/*-***************************************************************************
*  Streaming decompression howto
*
*  A ZBUFFv07_DCtx object is required to track streaming operations.
*  Use ZBUFFv07_createDCtx() and ZBUFFv07_freeDCtx() to create/release resources.
*  Use ZBUFFv07_decompressInit() to start a new decompression operation,
*   or ZBUFFv07_decompressInitDictionary() if decompression requires a dictionary.
*  Note that ZBUFFv07_DCtx objects can be re-init multiple times.
*
*  Use ZBUFFv07_decompressContinue() repetitively to consume your input.
*  *srcSizePtr and *dstCapacityPtr can be any size.
*  The function will report how many bytes were read or written by modifying *srcSizePtr and *dstCapacityPtr.
*  Note that it may not consume the entire input, in which case it's up to the caller to present remaining input again.
*  The content of `dst` will be overwritten (up to *dstCapacityPtr) at each function call, so save its content if it matters, or change `dst`.
*  @return : a hint to preferred nb of bytes to use as input for next function call (it's only a hint, to help latency),
*            or 0 when a frame is completely decoded,
*            or an error code, which can be tested using ZBUFFv07_isError().
*
*  Hint : recommended buffer sizes (not compulsory) : ZBUFFv07_recommendedDInSize() and ZBUFFv07_recommendedDOutSize()
*  output : ZBUFFv07_recommendedDOutSize== 128 KB block size is the internal unit, it ensures it's always possible to write a full block when decoded.
*  input  : ZBUFFv07_recommendedDInSize == 128KB + 3;
*           just follow indications from ZBUFFv07_decompressContinue() to minimize latency. It should always be <= 128 KB + 3 .
* *******************************************************************************/


/* *************************************
*  Tool functions
***************************************/
ZSTDLIB_API unsigned ZBUFFv07_isError(size_t errorCode);
ZSTDLIB_API const char* ZBUFFv07_getErrorName(size_t errorCode);

/** Functions below provide recommended buffer sizes for Compression or Decompression operations.
*   These sizes are just hints, they tend to offer better latency */
ZSTDLIB_API size_t ZBUFFv07_recommendedDInSize(void);
ZSTDLIB_API size_t ZBUFFv07_recommendedDOutSize(void);


/*-*************************************
*  Constants
***************************************/
#define ZSTDv07_MAGICNUMBER            0xFD2FB527   /* v0.7 */


#if defined (__cplusplus)
}
#endif

#endif  /* ZSTDv07_H_235446 */
