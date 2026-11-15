#include "naginata.h"

#include <stdio.h>

#include "gen740.h"
#include "naginata_keydata.h"

static const naginata_node_t *ng_current_node = &naginata_1;
static bool ng_char_emit = false;
// Emitted keys may remain held as continuous shifts, but are not fresh input.
static uint64_t ng_consumed_keys = 0;

static uint64_t ng_key_mask(uint16_t key) {
  return (uint64_t)1 << (key - NG_A);
}

static uint64_t ng_branch_mask(const naginata_node_t *node) {
  uint64_t mask = 0;
  while (node != NULL && node->parent != NULL) {
    mask |= ng_key_mask(node->key);
    node = node->parent;
  }
  return mask;
}

static bool ng_send_event(const uint16_t keys[], const uint8_t bounds) {
  bool flag = false;
  for (int8_t i = 0; i < bounds; i++) {
    if (keys[i] == KC_LANGUAGE_1) {
      tap_code(KC_LNG1);
      layer_move(L_NAG);
      flag = true;
    } else if (keys[i] == KC_LANGUAGE_2) {
      tap_code(KC_LNG2);
      layer_move(L_DVO);
      flag = true;
    } else {
      tap_code16(keys[i]);
      flag = true;
    }
  }
  return flag;
}

static bool ng_send_node(const naginata_node_t *node) {
  if (node == NULL) {
    return false;
  }
  const uint64_t mask = ng_branch_mask(node);
  if ((mask & ~ng_consumed_keys) == 0 ||
      !ng_send_event(node->keys, node->bounds)) {
    return false;
  }
  ng_consumed_keys |= mask;
  return true;
}

static bool ng_is_key_in_branch(const naginata_node_t *node, uint16_t key) {
  const naginata_node_t *n = node;
  while (n != NULL) {
    if (n->key == key) {
      return true;
    }
    n = n->parent;
  }
  return false;
}

bool process_naginata(uint16_t keycode, keyrecord_t *record) {
  switch (keycode) {
    case NG_A ... NG_RSFT3: {
      uint16_t ng_rollback_keybuf[8];
      uint8_t ng_rollback_keybuf_len = 0;

      if (record->event.pressed) {
        ng_consumed_keys &= ~ng_key_mask(keycode);
        ng_char_emit = false;
        const naginata_node_t *next_node = ng_current_node->next_node(keycode);
        const naginata_node_t *ng_rollback_root = ng_current_node;
        if (next_node == NULL) {
          while (ng_current_node->parent != NULL) {
            ng_rollback_keybuf[ng_rollback_keybuf_len++] = ng_current_node->key;
            ng_current_node = ng_current_node->parent;
            if (ng_current_node->next_node(keycode) != NULL) {
              ng_rollback_root = ng_current_node;
              const naginata_node_t *n = ng_current_node->next_node(keycode);
              if (n != NULL) {
                ng_current_node = ng_current_node->next_node(keycode);
              }
              break;
            }
          }
          for (int8_t i = ng_rollback_keybuf_len - 1; i >= 0; i--) {
            ng_send_node(ng_rollback_root->next_node(ng_rollback_keybuf[i]));
          }
        } else {
          ng_current_node = next_node;
        }
      } else {
        if (ng_current_node->key == keycode) {
          if (!ng_char_emit) {
            ng_char_emit = ng_send_node(ng_current_node);
            // An empty prefix with only consumed ancestors must not swallow
            // its fresh leaf when that leaf is released before the ancestors.
            const uint64_t mask = ng_branch_mask(ng_current_node);
            if (!ng_char_emit && ng_current_node->bounds == 0 &&
                (mask & ng_consumed_keys) != 0 &&
                (mask & ~ng_consumed_keys) == ng_key_mask(keycode)) {
              ng_char_emit = ng_send_node(naginata_1.next_node(keycode));
            }
          }
          ng_current_node = ng_current_node->parent;
        } else if (ng_is_key_in_branch(ng_current_node, keycode)) {
          if (!ng_char_emit) {
            ng_char_emit = ng_send_node(ng_current_node);
          }
          while (ng_current_node->parent != NULL) {
            if (ng_current_node->key == keycode) {
              if (!ng_char_emit) {
                ng_send_node(ng_current_node);
              }
              ng_current_node = ng_current_node->parent;
              break;
            } else {
              ng_rollback_keybuf[ng_rollback_keybuf_len++] =
                  ng_current_node->key;
              ng_current_node = ng_current_node->parent;
            }
          }
          for (int8_t i = ng_rollback_keybuf_len - 1; i >= 0; i--) {
            const naginata_node_t *n =
                ng_current_node->next_node(ng_rollback_keybuf[i]);
            if (n == NULL) {
              break;
            }
            ng_current_node = n;
          }
        }
        ng_consumed_keys &= ~ng_key_mask(keycode);
      }
    }
  }
  return true;
}
