// Host-only QMK I/O stubs; both the runtime and generated trie are real C.
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "../naginata_keydata.c"
#ifndef NG_RUNTIME_SOURCE
#    define NG_RUNTIME_SOURCE "../naginata.c"
#endif
#include NG_RUNTIME_SOURCE

static uint16_t output[256];
static size_t output_len;

void tap_code16(uint16_t key) {
    if (output_len == sizeof(output) / sizeof(output[0])) {
        abort();
    }
    output[output_len++] = key;
}

void tap_code(uint8_t key) {
    tap_code16(key);
}

void layer_move(uint8_t layer) {
    (void)layer;
}

static uint16_t input_key(const char *name, size_t len) {
    if (len == 1 && name[0] >= 'A' && name[0] <= 'Z') {
        return NG_A + name[0] - 'A';
    }
#define NAMED_KEY(k) if (len == strlen(#k) && !strncmp(name, #k, len)) return NG_##k
    NAMED_KEY(LSFT1);
    NAMED_KEY(LSFT2);
    NAMED_KEY(LSFT3);
    NAMED_KEY(RSFT1);
    NAMED_KEY(RSFT2);
    NAMED_KEY(RSFT3);
    NAMED_KEY(COMM);
    NAMED_KEY(DOT);
    NAMED_KEY(SLSH);
    NAMED_KEY(SCLN);
#undef NAMED_KEY
    fprintf(stderr, "Unknown key: %.*s\n", (int)len, name);
    exit(2);
}

int main(int argc, char **argv) {
    for (int i = 1; i < argc; ++i) {
        const size_t len = strlen(argv[i]);
        if (len < 2 || (argv[i][len - 1] != '+' && argv[i][len - 1] != '-')) {
            return 2;
        }
        const uint16_t key = input_key(argv[i], len - 1);
        keyrecord_t record = {.event = {.pressed = argv[i][len - 1] == '+'}};
        output_len = 0;
        if (!process_naginata(key, &record)) {
            return 3;
        }
        for (size_t j = 0; j < output_len; ++j) {
            printf("%u ", output[j]);
        }
        putchar('\n');
    }
    return 0;
}
