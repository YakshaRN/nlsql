# NLSQL API Test Scenarios

This document outlines test scenarios for evaluating the user experience of the NLSQL API.

## Quick Start

1. Import `postman_collection.json` into Postman
2. Set `base_url` variable to your API URL (default: `http://localhost:8000`)
3. Run collections in order to test different user patterns

---

## Test Categories

### 1. Basic Queries - Direct Questions
**Purpose:** Test well-formed questions with complete information

| # | Question | Expected Behavior |
|---|----------|-------------------|
| 1.1 | "What is the peak probability of GSI exceeding 0.60 over the next 14 days starting from 2026-01-15 12:00?" | EXECUTE - GSI_PEAK_PROBABILITY_14_DAYS |
| 1.2 | "Show me the tightest hour - the hour with highest average GSI - starting from 2026-01-15 12:00" | EXECUTE - TIGHTEST_HOUR_GSI |
| 1.3 | "What is the P01 extreme cold temperature forecast for RTO for the next 10 days starting 2026-01-20 00:00?" | EXECUTE - P01_EXTREME_COLD_TEMP_FORECAST |
| 1.4 | "What is the probability of Dunkelflaute from 2026-01-18 12:00?" | EXECUTE - PROBABILITY_DUNKELFLAUTE |

---

### 2. Vague Questions - Need Clarification
**Purpose:** Test how LLM guides users toward valid queries

| # | Question | Expected Behavior |
|---|----------|-------------------|
| 2.1 | "What about the evening?" | NEED_MORE_INFO - Should ask what about evening (GSI? Wind? Load?) |
| 2.2 | "Show me the forecast" | NEED_MORE_INFO - Should ask which forecast type |
| 2.3 | "What is the GSI probability for the next 14 days?" | NEED_MORE_INFO - Missing initialization timestamp |
| 2.4 | "What's happening tomorrow?" | NEED_MORE_INFO - Should ask what data they want |
| 2.5 | "Tell me about Houston zone" | NEED_MORE_INFO - Zone mentioned but no variable specified |

---

### 3. Follow-up Questions - Context Reuse
**Purpose:** Test conversation memory and parameter reuse

| Turn | Question | Expected Behavior |
|------|----------|-------------------|
| 3.1 | "What is the probability of GSI exceeding 0.60 during evening ramp for the next week starting 2026-01-15 12:00?" | EXECUTE - Sets context |
| 3.2 | "What about if GSI threshold is 0.75?" | EXECUTE - Reuses initialization, changes threshold |
| 3.3 | "Same thing but for January 20th" | EXECUTE - Same query_id, new date |
| 3.4 | "Now show me the tightest hour" | EXECUTE - New query, reuses initialization |
| 3.5 | "What's the average net demand during that hour?" | May need context interpretation |

---

### 4. Out of Scope Questions
**Purpose:** Test polite redirection for unsupported queries

| # | Question | Expected Behavior |
|---|----------|-------------------|
| 4.1 | "What will the electricity price be tomorrow?" | OUT_OF_SCOPE - No price data |
| 4.2 | "What was the actual load yesterday?" | OUT_OF_SCOPE - Only forecasts, no actuals |
| 4.3 | "Why is GSI high during cold snaps?" | OUT_OF_SCOPE - Explanation not data query |
| 4.4 | "What's the GSI for PJM?" | OUT_OF_SCOPE - Only ERCOT supported |
| 4.5 | "What's the weather in New York?" | OUT_OF_SCOPE - Completely unrelated |

---

### 5-9. Category Coverage Tests

Test at least one query from each of the 5 categories:

#### Category 1: GSI (Grid Stress)
- Peak probability, P99 peaks, evening ramp, stress paths, duration

#### Category 2: Load & Temperature  
- P01 cold, load during cold, zone freezing, sensitivity, load exceeds threshold

#### Category 3: Renewables
- Dunkelflaute, P10 wind, wind ramps, solar at risk, curtailment paths

#### Category 4: Zonal
- Zone spreads, export constraints, zone volatility, correlations

#### Category 5: Advanced/Tails
- Net demand probability, uncertainty ranges, tail risk, volatility peaks

---

### 10. Natural Language Variations
**Purpose:** Test different phrasing styles

| Style | Example |
|-------|---------|
| Casual | "How stressed is the grid going to be tonight?" |
| Colloquial | "Is it going to be really cold next week?" |
| Business | "What's the risk of high grid stress lasting multiple hours?" |
| Abbreviated | "GSI prob above 0.6 for 14 days from Jan 15 2026 noon" |
| Wordy | "I'm worried about solar generation being low. Can you show me..." |

---

### 11. Extended Conversation (15 turns)
**Purpose:** Test context memory over long conversations

Simulates a realistic user session exploring:
1. GSI questions (turns 1-3)
2. Temperature pivot (turns 4-6)
3. Renewables exploration (turns 7-9)
4. Back to GSI context (turns 10-12)
5. Advanced queries (turns 13-15)

---

### 12. Edge Cases
**Purpose:** Test boundary conditions

| # | Test | Expected Behavior |
|---|------|-------------------|
| 12.1 | Empty question | Should handle gracefully |
| 12.2 | Just punctuation "???" | NEED_MORE_INFO or error |
| 12.3 | "Same for..." without prior context | NEED_MORE_INFO - No previous query |
| 12.4 | Invalid location (Dallas) | Should correct or explain valid locations |
| 12.5 | Very long question | Should extract intent correctly |
| 12.6 | Typos "whats teh GSI probabiilty" | Should handle gracefully |

---

## Session IDs Used

| Session ID | Purpose |
|------------|---------|
| `test-session-001` | Basic queries |
| `vague-test-001` | Vague questions |
| `followup-test-001` | Follow-up testing |
| `oos-test-001` | Out of scope |
| `gsi-test-001` | GSI category |
| `load-test-001` | Load/temp category |
| `renew-test-001` | Renewables category |
| `zonal-test-001` | Zonal category |
| `tail-test-001` | Tails category |
| `natural-test-001` | Natural language |
| `extended-conv-001` | Extended conversation |
| `edge-test-001` | Edge cases |

---

## Evaluation Criteria

For each test, evaluate:

1. **Correct Decision**: Did it return the right decision type?
2. **Correct Query ID**: For EXECUTE, was the right query matched?
3. **Parameter Handling**: Were parameters extracted/reused correctly?
4. **Helpful Clarifications**: For NEED_MORE_INFO, was the question helpful?
5. **Polite Scoping**: For OUT_OF_SCOPE, did it redirect constructively?
6. **Response Time**: How long did the LLM take?

---

## Memory Configuration

The conversation context now supports up to **25 turns** (increased from 5).

To modify, edit `MAX_HISTORY_TURNS` in `/app/context/memory.py`.
