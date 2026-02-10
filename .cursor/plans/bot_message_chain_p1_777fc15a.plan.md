---
name: Bot Message Chain P1
overview: "Implement the synchronous (direct-response) part of the new bot message chain: m1, m3, m4.1/4.2, m6, m7.1-m7.3, m8, m9, m11, m13, m14, plus all keyboards, Firestore fields, PRO mode at 6 energy, starter pack, and downsell pack. Delayed messages (m2, m5, m10.x, m12) are deferred to Plan 2."
todos:
  - id: p1-firestore
    content: Add new user fields to create_user() and helper functions in both bot/ and backend/ firestore.py
    status: completed
  - id: p1-messages
    content: Create bot/messages.py with all 14 message text templates (HTML formatted)
    status: completed
  - id: p1-keyboards
    content: Rewrite bot/keyboards.py with all inline keyboard builders for the chain
    status: completed
  - id: p1-start
    content: Rewrite bot/handlers/start.py for m1 (/start) and m13 (/menu)
    status: completed
  - id: p1-template
    content: Create bot/handlers/template_selection.py for m3, m4.1, m4.2, mode toggle, webapp data
    status: completed
  - id: p1-photo
    content: "Rewrite bot/handlers/photo.py: PRO=6, m6, m7.x, m8, m9, m11, repeat, download"
    status: completed
  - id: p1-energy
    content: Create bot/handlers/energy.py for pack purchases, m13, m14, navigation
    status: completed
  - id: p1-backend-packs
    content: Add starter pack (100/990) and downsell (8/169) to backend payments
    status: completed
  - id: p1-placeholders
    content: Add 2 placeholder styles in bot/styles_data.py for template grid buttons
    status: completed
  - id: p1-wiring
    content: Update __init__.py and main.py to register new routers, fix import order
    status: completed
  - id: p1-deploy-test
    content: Deploy to dev and verify the full synchronous flow works
    status: completed
isProject: false
---

# Plan 1: Bot Message Chain -- Synchronous Flow

Implement all messages that fire as a **direct response** to user actions (no timers/cron). Delayed messages (m2, m5, m10.1, m10.2, m12) are left for Plan 2.

---

## Scope

| Message | Trigger |

|---------|---------|

| m1 | `/start` |

| m3 (OM) | template selected, 0 successful generations |

| m4.1 | template selected, >=1 gen, normal mode |

| m4.2 | template selected, >=1 gen, PRO mode |

| m6 | photo received, generation starts |

| m7.1 (OM) | generation success, count == 1 |

| m7.2 (OM) | generation success, count == 2 |

| m7.3 (OM) | generation success, count == 3 |

| m8 | generation success, count > 3 |

| m9 | insufficient energy + new user + has >=1 gen + not shown before |

| m11 | insufficient energy (all other cases) |

| m13 | `/menu` command or "Главное меню" button |

| m14 | "Пополнить баланс" / "Другие пакеты" button |

---

## Key Changes

### 1. Firestore: new user fields and helpers

In `[backend/firestore.py](backend/firestore.py)` `create_user()` -- add default fields:

```python
"successful_generations": 0,
"is_new_user": True,      # never bought any pack
"starter_pack_purchased": False,
"m9_shown": False,
"m7_1_sent": False,
"m7_2_sent": False,
"m7_3_sent": False,
```

In `[bot/firestore.py](bot/firestore.py)` -- add helper functions:

- `increment_successful_generations(telegram_id)` -- atomic increment, returns new count
- `set_user_flag(telegram_id, flag_name, value)` -- generic flag setter
- `ensure_user_exists(telegram_id, username)` -- create if not exists (called from `/start`)

### 2. New file: `bot/messages.py`

All 14 message text templates as functions returning formatted HTML strings. Each function accepts the dynamic parts (template name, energy balance, username, etc.) and returns ready-to-send text. Uses HTML parse mode (consistent with current bot default).

### 3. Rewrite: `bot/keyboards.py`

Replace existing keyboards with:

| Builder function | Used in | Buttons |

|---|---|---|

| `kb_template_grid()` | m1, m2, m10.x | 2 real style buttons (ice_cube, winter_triptych) + 2 placeholders + "Смотреть все шаблоны" (miniapp) |

| `kb_config_onboarding(style_id)` | m3 | "Сменить шаблон" |

| `kb_config_normal(style_id)` | m4.1 | "PRO-режим" + "Сменить шаблон" |

| `kb_config_pro(style_id)` | m4.2 | "Обычный режим" + "Сменить шаблон" |

| `kb_result_m71(style_id)` | m7.1 | "Скачать" + "Повторить 1" + "Сменить шаблон" |

| `kb_result_m72(style_id)` | m7.2 | "Скачать" + "Повторить 1" + "Сменить шаблон" + "Пополнить баланс" |

| `kb_result_m73(style_id)` | m7.3 | same as m72 |

| `kb_result_m8(style_id)` | m8 | "Скачать" + "Повторить 1" + "Сменить шаблон" + "Пополнить баланс" |

| `kb_starter_pack()` | m9 | "Забрать 100 за 990" + "Другие пакеты" |

| `kb_insufficient(back)` | m11 | 4 pack buttons + "Главное меню" |

| `kb_menu()` | m13 | "Выбрать шаблон" + "Пополнить баланс" |

| `kb_balance(back_target)` | m14 | "Назад" + 4 pack buttons + "Связаться с менеджером" |

Template buttons use `callback_data="tpl:{style_id}"`. Placeholder buttons use `callback_data="tpl:placeholder"`.

### 4. Rewrite: `[bot/handlers/start.py](bot/handlers/start.py)`

- `/start` -- call `ensure_user_exists()`, send m1 with `kb_template_grid()`
- `/menu` -- send m13 with `kb_menu()`
- Keep dev miniapp callback

### 5. New file: `bot/handlers/template_selection.py`

Handles all template/mode callbacks:

- `tpl:{style_id}` -- look up style, check `successful_generations`:
  - 0 -> send m3 + `kb_config_onboarding`, set FSM `awaiting_photo` with style data
  - > =1 -> send m4.1 + `kb_config_normal`, set FSM `awaiting_photo`
- `tpl:placeholder` -> answer "Скоро!"
- `toggle_pro:{style_id}` -> send m4.2 + `kb_config_pro`, update FSM mode to pro
- `toggle_normal:{style_id}` -> send m4.1 + `kb_config_normal`, update FSM mode to normal
- `change_template` -> open miniapp or send link
- Also absorb current `[bot/handlers/webapp.py](bot/handlers/webapp.py)` logic (mini app data handler) adapted to send m3/m4.x instead of old message

### 6. Rewrite: `[bot/handlers/photo.py](bot/handlers/photo.py)`

**PRO cost change: 2 -> 6 energy**

Flow when photo is received:

1. Get style/mode from FSM (or pending selection)
2. Calculate cost: `6 if mode == "pro" else 1`
3. Check balance:
  - If insufficient: check conditions -> send m9 or m11 (see below), return to idle
4. Deduct energy atomically
5. Send m6 ("Генерируем...")
6. Call Vertex AI `generate_single()`
7. Delete m6 status message
8. On success:
  - `increment_successful_generations()` -> get new count
  - count == 1 and m7_1 not sent -> send m7.1, mark m7_1_sent
  - count == 2 and m7_2 not sent -> send m7.2, mark m7_2_sent
  - count == 3 and m7_3 not sent -> send m7.3, mark m7_3_sent
  - otherwise -> send m8
9. On failure: refund energy, send error

Insufficient energy logic (step 3):

- If `is_new_user` and `successful_generations >= 1` and not `m9_shown` -> send m9, set `m9_shown = True`
- Otherwise -> send m11

New callback handlers in this file:

- `repeat:{style_id}` -- re-enter generation flow (set FSM awaiting_photo with same style, send m4.1/m4.2)
- `download:{file_id}` -- send the generated photo as a document for full-quality download

### 7. New file: `bot/handlers/energy.py`

Handles purchase and menu callbacks:

- `buy_pack:{pack_id}` -- call backend `/api/payments/create-pack-payment`, return payment URL/widget params
- `buy_starter` -- same but for starter pack (pack_starter), also set `starter_pack_purchased = True` on success
- `buy_downsell` -- same for downsell pack (pack_downsell)
- `show_menu` -- send m13
- `show_balance:{back_target}` -- send m14 with back button context
- `back:{target}` -- navigate back to the message that opened m14
- `contact_manager` -- send support contact info

### 8. Update: `[bot/handlers/__init__.py](bot/handlers/__init__.py)`

Register new routers: `template_selection_router`, `energy_router`.

### 9. Update: `[bot/main.py](bot/main.py)`

Import and include new routers in the dispatcher. Order matters -- template_selection before photo (callbacks vs message handlers).

### 10. Backend: new packs

In `[backend/routers/payments.py](backend/routers/payments.py)` add to `GENERATION_PACKS`:

```python
{"id": "pack_starter", "energy": 100, "price": 990, "currency": "RUB", "badge": "стартер-пак", "one_time": True},
{"id": "pack_downsell", "energy": 8, "price": 169, "currency": "RUB", "badge": "пробный", "one_time": True},
```

### 11. Placeholder styles

In `[bot/styles_data.py](bot/styles_data.py)` add 2 placeholder entries (id `placeholder_3`, `placeholder_4`) with `"placeholder": True` flag and no prompt. The keyboard builder references these for the 2 extra template buttons. When selected, bot answers "Этот шаблон скоро появится!".

### 12. States

`[bot/states.py](bot/states.py)` -- keep existing 3 states (idle, awaiting_photo, generating). No new states needed; all routing is via callback_data and Firestore flags.

---

## What is NOT in this plan (deferred to Plan 2)

- m2 (1h after welcome)
- m5 (7min after template selection without photo)
- m10.1 (60min after 1st gen)
- m10.2 (60min after 2nd gen)
- m12 (24h after m9 if no purchase)
- Spinning emoji animation in m6
- Video/image media assets for m1, m2, m3, etc.
- Cron endpoint for delayed messages

