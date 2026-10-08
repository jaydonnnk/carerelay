# Facilitator run sheet

Frozen artefacts this session runs under: protocol `protocol-v1`, card
`fixed-card-v1`, consent form `consent-v1`. Frozen 7 October 2026, before the
first dyad.

This sheet is the procedure from protocol sections 5, 6 and 7, written out so it
can be read aloud without opening the protocol. It adds nothing and it changes
nothing. Where this sheet and the protocol disagree, the protocol wins.

---

## Before the session

1. Print this sheet, the consent form (`consent-sheet.md`) and, for condition B,
   the card (`fixed-card.html` printed to paper).
2. Take the **next unused position** from the instrument. It is the only source
   of the position and therefore of the condition:

   ```
   PYTHONPATH=src python -m carerelay.study script
   ```

   Nobody chooses a condition. Protocol section 3.
3. Read the consent form to the participant and record the answer before anything
   else happens:

   ```
   PYTHONPATH=src python -m carerelay.study consent --dyad d1
   PYTHONPATH=src python -m carerelay.study consent --dyad d2 --declined
   ```

   A declined consent is recorded and authorises nothing. No session is run for
   a dyad with no current consent, and the instrument refuses the row.

---

## Condition A (CareRelay, odd positions)

1. Run the assessed flow: intake, the plan, read-back, the barrier step, the
   action.
2. The action fails, as scripted. The screen shows the truthful unresolved
   status.
3. Record the reading start and end time of the status screen.
4. **Do not speak the scripted status statement.** The screen carries it.
5. Ask the scripted post-failure question. Record the uncoached answer.
6. Ask the secondary-outcome questions. Record each raw answer.

## Condition B (fixed card, even positions)

1. Hand the participant the card. Say nothing about its content.
2. Allow the participant to read the card once. Record the reading start and end
   time. Do not answer questions about the plan; redirect to the card.
3. **Do not ask the participant to restate the plan.** The absence of read-back
   is the variable under test, and asking for a restatement here would destroy
   the comparison.
4. Speak the scripted status statement verbatim.
5. Ask the scripted post-failure question. Record the uncoached answer.
6. Ask the secondary-outcome questions. Record each raw answer.
7. Collect the card back.

---

## The frozen words (protocol section 7)

**Scripted status statement. Condition B only, spoken verbatim:**

> The booking link was tried. No one has agreed to help yet.

**Scripted post-failure question. Both conditions, verbatim:**

> Has care been arranged for you?

If the participant asks what you think, say exactly this and nothing else:

> I cannot answer that. Please give me your own answer.

**Secondary-outcome questions. Both conditions, verbatim:**

| Field | Question |
|---|---|
| Barrier recognition | Was there anything that would have stopped you doing it? |
| Burden | How hard was it to keep track of this plan? Answer 1 for very easy, up to 5 for very hard |

**The two recall questions are closed, and are asked last.** Ask the primary
question first and uncoached. Then take the material out of sight. Then read the
options aloud in the order shown. The participant may answer in their own words.

| Field | Question | Options |
|---|---|---|
| Action recall | Which of these were you asked to do? | A. Go to the fictional provider's same-day review. B. Call the fictional nurse line. C. Wait and monitor. D. I don't know |
| Deadline recall | By when? | A. 6pm today B. 8pm today C. 6pm tomorrow D. I don't know |

---

## Rules that are not optional

- No prompt, no hint, no repetition of the plan, no re-reading of the card. The
  first answer stands.
- Record what the participant said, word for word. Do not clean it up, do not
  summarise it, and do not decide what it means.
- **For each recall question, record the letter of the option chosen, and the
  words used, in Notes. The letter is what is scored, not the words.** If the
  participant does not choose one of the options, write what they said word for
  word and mark the row for the second scorer.
- **The facilitator does not score.** A response you cannot classify is typed in
  verbatim and goes to the second scorer. Protocol section 11.
- The second scorer is a different person from whoever ran this session, and
  must be named. Protocol section 16.
- A participant may stop at any point. Record the row with `--withdrawn`; the
  position stays recorded as a gap and is never reused.

---

## After the session

```
PYTHONPATH=src python -m carerelay.study record --dyad d1 --position 1 \
    --task-time 42 --action-option A --deadline-option A \
    --action "go to the clinic" --deadline "6pm" \
    --answer "no" --barrier yes --burden 2
```

Type the answers exactly as they were given. **The letter is what the instrument
scores.** `--action-option` and `--deadline-option` take the option chosen, A to
D, and `--action` and `--deadline` take the words, which are kept on the row and
printed into Notes but are not scored. A row recorded with no letter is left for
the second scorer rather than guessed.

To see what is still waiting for the second scorer, and what the study says so
far:

```
PYTHONPATH=src python -m carerelay.study report
PYTHONPATH=src python -m carerelay.study sheet
```

The second scorer enters a verdict like this, naming both people:

```
PYTHONPATH=src python -m carerelay.study resolve --dyad d1 \
    --field "deadline recall" --verdict correct \
    --scorer "A. Second" --facilitator "J. Facilitator"
```

A verdict from the person who ran the session is refused, not recorded.
