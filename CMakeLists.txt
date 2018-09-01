# Dmitriy Vetutnev, ODNAT 2018

cmake_minimum_required(VERSION 3.0)
set(CMAKE_ALLOW_LOOSE_LOOP_CONSTRUCTS ON)

project(zlib C)

include(${CMAKE_BINARY_DIR}/conanbuildinfo.cmake)
conan_basic_setup()

set(VERSION "1.2.11")

option(ASM686 "Enable building i686 assembly implementation")
option(AMD64 "Enable building amd64 assembly implementation")

include(CheckTypeSize)
include(CheckFunctionExists)
include(CheckIncludeFile)
include(CheckCSourceCompiles)

check_include_file(sys/types.h HAVE_SYS_TYPES_H)
check_include_file(stdint.h    HAVE_STDINT_H)
check_include_file(stddef.h    HAVE_STDDEF_H)

#
# Check to see if we have large file support
#
set(CMAKE_REQUIRED_DEFINITIONS -D_LARGEFILE64_SOURCE=1)
# We add these other definitions here because CheckTypeSize.cmake
# in CMake 2.4.x does not automatically do so and we want
# compatibility with CMake 2.4.x.
if(HAVE_SYS_TYPES_H)
    list(APPEND CMAKE_REQUIRED_DEFINITIONS -DHAVE_SYS_TYPES_H)
endif()
if(HAVE_STDINT_H)
    list(APPEND CMAKE_REQUIRED_DEFINITIONS -DHAVE_STDINT_H)
endif()
if(HAVE_STDDEF_H)
    list(APPEND CMAKE_REQUIRED_DEFINITIONS -DHAVE_STDDEF_H)
endif()
check_type_size(off64_t OFF64_T)
if(HAVE_OFF64_T)
   add_definitions(-D_LARGEFILE64_SOURCE=1)
endif()
set(CMAKE_REQUIRED_DEFINITIONS) # clear variable

#
# Check for fseeko
#
check_function_exists(fseeko HAVE_FSEEKO)
if(NOT HAVE_FSEEKO)
    add_definitions(-DNO_FSEEKO)
endif()

#
# Check for unistd.h
#
check_include_file(unistd.h Z_HAVE_UNISTD_H)

if(MSVC)
    set(CMAKE_DEBUG_POSTFIX "d")
    add_definitions(-D_CRT_SECURE_NO_DEPRECATE)
    add_definitions(-D_CRT_NONSTDC_NO_DEPRECATE)
    include_directories(${CMAKE_CURRENT_SOURCE_DIR}/src)
endif()

if(NOT CMAKE_CURRENT_SOURCE_DIR STREQUAL CMAKE_CURRENT_BINARY_DIR)
    # If we're doing an out of source build and the user has a zconf.h
    # in their source tree...
    if(EXISTS ${CMAKE_CURRENT_SOURCE_DIR}/src/zconf.h)
        message(STATUS "Renaming")
        message(STATUS "    ${CMAKE_CURRENT_SOURCE_DIR}/src/zconf.h")
        message(STATUS "to 'zconf.h.included' because this file is included with zlib")
        message(STATUS "but CMake generates it automatically in the build directory.")
        file(RENAME ${CMAKE_CURRENT_SOURCE_DIR}/src/zconf.h ${CMAKE_CURRENT_SOURCE_DIR}/src/zconf.h.included)
  endif()
endif()

set(ZLIB_PC ${CMAKE_CURRENT_BINARY_DIR}/src/zlib.pc)
configure_file( ${CMAKE_CURRENT_SOURCE_DIR}/src/zlib.pc.cmakein
		${ZLIB_PC} @ONLY)
configure_file(	${CMAKE_CURRENT_SOURCE_DIR}/src/zconf.h.cmakein
		${CMAKE_CURRENT_BINARY_DIR}/src/zconf.h @ONLY)
include_directories(${CMAKE_CURRENT_BINARY_DIR}/src ${CMAKE_SOURCE_DIR}/src)


#============================================================================
# zlib
#============================================================================

set(ZLIB_PUBLIC_HDRS
    ${CMAKE_CURRENT_BINARY_DIR}/src/zconf.h
    src/zlib.h
)
set(ZLIB_PRIVATE_HDRS
    src/crc32.h
    src/deflate.h
    src/gzguts.h
    src/inffast.h
    src/inffixed.h
    src/inflate.h
    src/inftrees.h
    src/trees.h
    src/zutil.h
)
set(ZLIB_SRCS
    src/adler32.c
    src/compress.c
    src/crc32.c
    src/deflate.c
    src/gzclose.c
    src/gzlib.c
    src/gzread.c
    src/gzwrite.c
    src/inflate.c
    src/infback.c
    src/inftrees.c
    src/inffast.c
    src/trees.c
    src/uncompr.c
    src/zutil.c
)

if(NOT MINGW)
    set(ZLIB_DLL_SRCS
        src/win32/zlib1.rc # If present will override custom build rule below.
    )
endif()

if(CMAKE_COMPILER_IS_GNUCC)
    if(ASM686)
        set(ZLIB_ASMS src/contrib/asm686/match.S)
    elseif (AMD64)
        set(ZLIB_ASMS src/contrib/amd64/amd64-match.S)
    endif ()

	if(ZLIB_ASMS)
		add_definitions(-DASMV)
		set_source_files_properties(${ZLIB_ASMS} PROPERTIES LANGUAGE C COMPILE_FLAGS -DNO_UNDERLINE)
	endif()
endif()

if(MSVC)
    if(ASM686)
		ENABLE_LANGUAGE(ASM_MASM)
        set(ZLIB_ASMS
			src/contrib/masmx86/inffas32.asm
			src/contrib/masmx86/match686.asm
		)
    elseif (AMD64)
		ENABLE_LANGUAGE(ASM_MASM)
        set(ZLIB_ASMS
			src/contrib/masmx64/gvmat64.asm
			src/contrib/masmx64/inffasx64.asm
		)
    endif()

	if(ZLIB_ASMS)
		add_definitions(-DASMV -DASMINF)
	endif()
endif()

# parse the full version number from zlib.h and include in ZLIB_FULL_VERSION
file(READ ${CMAKE_CURRENT_SOURCE_DIR}/src/zlib.h _zlib_h_contents)
string(REGEX REPLACE ".*#define[ \t]+ZLIB_VERSION[ \t]+\"([-0-9A-Za-z.]+)\".*"
    "\\1" ZLIB_FULL_VERSION ${_zlib_h_contents})

if(MINGW)
    # This gets us DLL resource information when compiling on MinGW.
    if(NOT CMAKE_RC_COMPILER)
        set(CMAKE_RC_COMPILER windres.exe)
    endif()

    add_custom_command(OUTPUT ${CMAKE_CURRENT_BINARY_DIR}/src/zlib1rc.obj
                       COMMAND ${CMAKE_RC_COMPILER}
                            -D GCC_WINDRES
                            -I ${CMAKE_CURRENT_SOURCE_DIR}/src
                            -I ${CMAKE_CURRENT_BINARY_DIR}/src
                            -o ${CMAKE_CURRENT_BINARY_DIR}/src/zlib1rc.obj
                            -i ${CMAKE_CURRENT_SOURCE_DIR}/src/win32/zlib1.rc)
    set(ZLIB_DLL_SRCS ${CMAKE_CURRENT_BINARY_DIR}/src/zlib1rc.obj)
endif(MINGW)

if(BUILD_SHARED_LIBS)
    add_library(zlib SHARED ${ZLIB_SRCS} ${ZLIB_ASMS} ${ZLIB_DLL_SRCS} ${ZLIB_PUBLIC_HDRS} ${ZLIB_PRIVATE_HDRS})

    set_target_properties(zlib PROPERTIES DEFINE_SYMBOL ZLIB_DLL)
    set_target_properties(zlib PROPERTIES SOVERSION 1)

    if(NOT CYGWIN)
    # This property causes shared libraries on Linux to have the full version
    # encoded into their final filename.  We disable this on Cygwin because
    # it causes cygz-${ZLIB_FULL_VERSION}.dll to be created when cygz.dll
    # seems to be the default.
    #
    # This has no effect with MSVC, on that platform the version info for
    # the DLL comes from the resource file win32/zlib1.rc
        set_target_properties(zlib PROPERTIES VERSION ${ZLIB_FULL_VERSION})
    endif()
    if(UNIX)
        set_target_properties(zlib PROPERTIES OUTPUT_NAME z)
        if(NOT APPLE)
            set_target_properties(zlib PROPERTIES LINK_FLAGS "-Wl,--version-script,\"${CMAKE_CURRENT_SOURCE_DIR}/src/zlib.map\"")
        endif()
    endif()
    if(WIN32)
        set_target_properties(zlib PROPERTIES SUFFIX "1.dll")
        if (MSVC)
            set_target_properties(zlib PROPERTIES PDB_NAME_DEBUG zlibd)
        endif()
    endif()
else()
    add_library(zlibstatic STATIC ${ZLIB_SRCS} ${ZLIB_ASMS} ${ZLIB_PUBLIC_HDRS} ${ZLIB_PRIVATE_HDRS})
    if(UNIX)
        set_target_properties(zlibstatic PROPERTIES OUTPUT_NAME z)
    endif()
    if(WIN32 AND MSVC)
        set_target_properties(zlibstatic PROPERTIES COMPILE_PDB_NAME_DEBUG zlibstaticd)
    endif()
endif()

#============================================================================
# minizip
#============================================================================

option(ENABLE_MINIZIP "Enable minizip" OFF)
if(ENABLE_MINIZIP)
    set(MINIZIP_DIR ${CMAKE_CURRENT_SOURCE_DIR}/src/contrib/minizip)
    set(MINIZIP_SOURCES
        ${MINIZIP_DIR}/ioapi.c
        ${MINIZIP_DIR}/mztools.c
        ${MINIZIP_DIR}/unzip.c
        ${MINIZIP_DIR}/zip.c
    )
    set(MINIZIP_PUBLIC_HEADERS
        ${MINIZIP_DIR}/crypt.h
        ${MINIZIP_DIR}/ioapi.h
        ${MINIZIP_DIR}/mztools.h
        ${MINIZIP_DIR}/unzip.h
        ${MINIZIP_DIR}/zip.h
        ${MINIZIP_DIR}/minizip_extern.h
    )
    if(WIN32)
        list(APPEND MINIZIP_SOURCES ${MINIZIP_DIR}/iowin32.c)
        list(APPEND MINIZIP_PUBLIC_HEADERS ${MINIZIP_DIR}/iowin32.h)
    endif()
    set(MINIZIP_DLL_SOURCES ${MINIZIP_DIR}/minizip1.rc)

    if(BUILD_SHARED_LIBS)
        add_library(minizip SHARED ${MINIZIP_SOURCES} ${MINIZIP_DLL_SOURCES})
        target_link_libraries(minizip zlib)
        set_target_properties(minizip
            PROPERTIES
            INSTALL_RPATH "$ORIGIN"
            BUILD_WITH_INSTALL_RPATH True
        )
        if(UNIX)
            set_target_properties(minizip PROPERTIES OUTPUT_NAME minizip)
        endif()
        if(WIN32)
            set_target_properties(minizip PROPERTIES SUFFIX "1.dll")
            if(MSVC)
                set_target_properties(minizip PROPERTIES PDB_NAME_DEBUG minizipd)
            endif()
        endif()
        set_target_properties(minizip PROPERTIES DEFINE_SYMBOL MINIZIP_DLL)
        target_compile_definitions(minizip PRIVATE -DMINIZIP_BUILDING -DZLIB_DLL)
        set_target_properties(minizip PROPERTIES SOVERSION 1)
        if(NOT CYGWIN)
            set_target_properties(minizip PROPERTIES VERSION "1.1.0")
        endif()
    else()
        add_library(minizipstatic STATIC ${MINIZIP_SOURCES})
        if(WIN32 AND MSVC)
            set_target_properties(minizipstatic PROPERTIES COMPILE_PDB_NAME_DEBUG minizipstaticd)
        endif()
        if(UNIX)
            set_target_properties(minizipstatic PROPERTIES OUTPUT_NAME minizip)
        endif()
    endif()
endif()
