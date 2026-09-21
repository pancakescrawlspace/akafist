# Our own headword OCR — Kraken and `dj_hwocr.py`

An expository note (session 6, 2026-09-21): what option (C) of Phase 3b step 2 is (PLAN.md), how the tool it runs
on works, what `tools/dj_hwocr.py` prepares for it and why, and how to read a training run. Written for learning
the machine-learning side as much as for the record; the numbers are this data's, measured.

## 1. The problem

The Church Slavonic headwords are the one part of the book that no OCR reads. Over the twelve ground-truth pages
the best we have, the vote of the four witnesses, gets 139 of 325 headwords exactly right (norm level; 15.8 %
character error), against 1.1 % error in the definitions (eval/RESULTS.md). Three ways to read them are on the
table: (A) a vision model through the API, (B) reading contact sheets in interactive sessions, (C) a recogniser of
our own, taught this one book's types. (C) is free and local; it is also independent of (A) by construction,
which makes the two a pair: where they agree a headword can be trusted, where they differ is what gets proofread.

## 2. What a line recogniser does

It takes the image of **one printed line** and returns its text. It does not cut the line into letters first.
Instead the image is scaled to a fixed height (Kraken's default: 120 pixels; the width follows) and read from left
to right as a sequence of thin vertical slices, *frames*. For every frame the network gives a probability for every
symbol it knows, plus one extra symbol, the *blank* ("nothing new here"). Decoding takes the likeliest symbol per
frame, merges runs of the same symbol and drops the blanks:

    frames:   Б Б – а а – р – с с – у – к – ъ ъ
    result:   Барсукъ

(A real double letter needs a blank between its halves: `с – с`.) This scheme is called **CTC** (Connectionist
Temporal Classification). Its virtue is in training: the network is told only *which text* the line holds, never
*where* each letter is — it works out the alignment itself. So a training example is just a pair, image and text.

The price: the pair must match **exactly**. Every character of the text must be visible in the image and nothing
visible may be missing from the text, or the network is taught to see what isn't there. That is why `dj_hwocr.py`
works with whole printed lines, whose extent scan A's layout gives exactly, rather than with the headword crops of
`dj_crops.py` (cut to an *estimated* headword length); why lines on a side whose margin the scan cuts off are left
out; and why letters the GT reads in another copy (`‹…›`) are removed from the text of A's line image.

## 3. The network

Kraken describes a network in a one-line language, VGSL. Its default recogniser, the one we train, is

    [1,120,0,1 Cr3,13,32 Do0.1,2 Mp2,2 Cr3,13,32 Do0.1,2 Mp2,2 Cr3,9,64 Do0.1,2 Mp2,2 Cr3,9,64 Do0.1,2
     S1(1x0)1,3 Lbx200 Do0.1,2 Lbx200 Do0.1,2 Lbx200 Do]

read left to right:

| piece | what it does |
|---|---|
| `1,120,0,1` | the input: one line at a time, 120 px high, any width, one channel (greyscale) |
| `Cr3,13,32` | a *convolution*: 32 small detectors, each looking at a 3 × 13 pixel patch everywhere along the line, learning to respond to a stroke, a curve, a serif; `r` = ReLU (negative responses set to zero) |
| `Do0.1,2` | *dropout*: during training, 10 % of the detectors' outputs are switched off at random, so the network cannot come to depend on any single one — a guard against memorising |
| `Mp2,2` | *max-pooling*: halves height and width, keeping the strongest response in each 2 × 2 block — a summary that tolerates small shifts |
| (× 4) | four such stages (32, 32, 64, 64 detectors), three poolings: the 120 px become 15 rows of 64 features |
| `S1(1x0)1,3` | a reshape: the 15 × 64 values of each column become one vector — the image is now a sequence of frames, one per 8 pixels of the scaled line's width |
| `Lbx200` (× 3) | three layers of bidirectional *LSTM*, 200 units each way: they read the frame sequence forwards and backwards, so the decision at each frame can use what stands on both sides of it (is this stroke the end of ы, or ъ followed by і?) |
| (added) | the output layer: one unit per symbol of the alphabet, plus the blank |

In all **4.0 million** numbers (*weights*, *parameters*) — training is the search for good values of them. Kraken 7
also offers another architecture family (`--arch ppocrv6`, from PaddleOCR); we start with the default.

**The alphabet (codec)** is built from the training texts: every distinct character in them gets an output unit.
A character that never occurs in training can never be output. Our stage-1 labels are at the norm level (§ 6), so
this model's alphabet has no ѡ, ꙋ or ѧ — it reads Church Slavonic letters as their civil equivalents, which is what
lookup and linking need. The training labels have **169** distinct characters (Cyrillic, Greek, Latin, digits,
punctuation — 178 before the look-alikes were folded, § 6), so the network has 170 output symbols with the blank.
`dj_hwocr.py data` prints the count and writes the whole alphabet to `cache/hwocr/alphabet.tsv`, rarest first,
with each character's Unicode name and its counts in train, validation and test (`dj_hwocr.py alphabet` rewrites it
from the manifest alone). The rarest occur once — a single example teaches a network next to nothing, so it will
seldom write them; the list is also where a stray symbol shows first.

## 4. How training works

- **Loss.** For each line the network's frame probabilities say how likely the correct text is; the *CTC loss* is
  a measure of how unlikely. Training nudges all 4 million weights a little in the direction that lowers the loss
  (*gradient descent*; Kraken uses the AdamW optimiser with a *learning rate* — step size — of 0.001).
- **Batch and epoch.** Lines are processed 16 at a time (`-B 16`); one nudge per *batch*. One pass over all 16,799
  training lines is an *epoch*, about 1,050 batches. Measured here: ~1.5 batches a second on the Mac's GPU (MPS), so
  **~12 minutes an epoch**. Each epoch the lines come in a new random order.
- **Augmentation.** `--augment` distorts half the lines at random each time they are seen — up to three of: slight
  warping, ink eroded or spread, show-through from the other side, a ruling line, neighbouring lines' ascenders and
  descenders intruding, contrast and gamma changes, uneven lighting, noise, blur, a small patch erased (Kraken's
  recipe for historical lines). The network rarely sees the same image twice, so it has to learn the letters rather
  than the images.
- **Validation and early stopping.** After every epoch the network reads the 359 *validation* lines, which it never
  trains on, and Kraken reports `val_accuracy` = 1 − character error rate (and the same for words). A checkpoint
  is saved (`checkpoint_EE-0.XXXX.ckpt`, the best ten kept, 48 MB each). With `-q early` training stops when
  validation accuracy has not improved for 10 epochs (`--lag`), and the best checkpoint becomes the model
  (`best_0.XXXX.safetensors`, 16 MB).
- **Overfitting** is what early stopping guards against: the training loss keeps falling while validation accuracy
  stalls or drops — the network is memorising its training lines instead of learning to read. Dropout and
  augmentation push the same way.
- **At the start** a CTC network outputs blanks everywhere: after one epoch on a small sample the smoke test read
  0 % — normal. Accuracy climbs once the network has found the alignment.

## 5. The three sets and what each is for

| set | its job | here |
|---|---|---|
| **train** | what the weights are fitted to | 16,799 lines |
| **validation** | chooses when to stop and which checkpoint is best — so it is *used*, indirectly | 359 lines: the automatic lines of every 20th leaf |
| **test** | the verdict, and nothing else: no decision may look at it | 215 lines of the two **held-out GT pages**, p. 246 and p. 659 (leaves 283, 696), with 52 headwords |

Two cautions. The test is small: at 52 headwords one headword is two percentage points, so a difference of a few
points between two models means little. And the validation labels are automatic (§ 6), right in the head in ~83 %
of lines, so validation accuracy has a ceiling below 100 % and measures agreement with the vote as much as truth —
good enough to choose a checkpoint, not to judge a model. Nothing from the two held-out leaves is in any other set
(*leakage* would flatter the test), and the synthetic headwords are not drawn from them either. The other ten GT
pages are used for training: their exact labels are the most valuable we have, which means they can no longer
measure this model — only the held-out two can.

## 6. What `dj_hwocr.py` prepares

`python3 tools/dj_hwocr.py data` (several minutes; `--only synth` rebuilds one kind in ~20 s) writes into
`djachenko/cache/hwocr/` (git-ignored, ~1 GB): for each sample an image `ID.png` and its text `ID.gt.txt`, the form
`ketos train -f path` reads; `manifest.tsv` (one row per sample: id, set, split, leaf, first line or not, flags,
image, and the labels); and the lists `train.txt`, `val.txt`, `test.txt`. `dj_hwocr.py sheet SET` draws a contact
sheet of samples with their labels — the quickest check that image and text belong together.

**The images** are scan A's line boxes (+12 px), scaled from 600 to 400 ppi, greyscale, the paper brought to white
(the darkest 1 % stretched to black, the 60th percentile — a line image is mostly paper — to white).

**The labels** come at three levels. `norm` is what stage 1 trains on: Church Slavonic letters folded to civil
ones, look-alikes and dashes unified, оу → у, й → и, Greek without accents — the level at which the witnesses are
compared and the headwords benchmarked (`Азбꙋка` → `Азбука`, `еврейскихъ` → `евреискихъ`). On top of that, one
symbol per printed glyph: the OCR layers write look-alikes the book does not have — fita as Cyrillic barred o
(`ө`), І as palochka (`Ӏ`), Latin h and j as Cyrillic `һ` and `ј`, braces for brackets — and these are folded to
the book's letter, since a network taught two answers for one glyph can only guess between them; a Greek breathing
standing on its own is dropped like every other accent; an automatic line with OCR debris (`■`, a column rule read
as `|`) is left out. `strict` (letters as
printed, no accents) is kept wherever it is known — the GT and the synthetic lines — for stage 2. `marked` (with the
accents) exists for the synthetic lines only: the Phase 0 decision to leave accents and titla out is not final.

**Three kinds of sample:**

| kind | lines | labels | why |
|---|---:|---|---|
| **gt** | 1,094 train + 215 test | exact, from the ground truth; its `¦` markers pair each GT line with scan A's line one to one | the only exact labels; 259 first lines with a headword to train on |
| **agree** | 5,274 first lines + 2,431 continuation lines (train), 359 (val) | the voted text, where witnesses D and B read alike | real lines in the book's own types, in quantity |
| **synth** | 8,000 | exact by construction | the Church Slavonic letters the other two have too few of |

*agree.* A first line of an entry qualifies when D and B read its head identically (no `disputed` span before the
separator, VOTE.md); the rest of the line is the vote's. Requiring the whole line to agree would leave one first
line in ten — a comma or a dropped "=" is enough to disagree. Measured on the GT pages, where the truth is known:
**the automatic head is right in 83 % of lines (35 of 42), the whole line's characters in 98.85 %.** That is label
noise, and deliberate: a network trained on thousands of mostly right labels learns the rule, not the exceptions.
But these heads are the easy ones — the ones two OCRs could read — so they teach little about the hard glyphs.
A sample of 8 % of the continuation lines, those D and B read alike throughout (right in ~99.9 %), adds the
book's civil type. Left
out: a column side whose margin the scan cuts off, a line touching the image edge, a line whose label is much
longer or shorter than ABBYY's reading of it (a line start carried over badly).

*synth.* Typst sets a first line: a head in one of five Church Slavonic faces of the fonts-cu family (OFL) —
Ponomar, Pochaevsk and Monomakh, which the book's headword type resembles, Menaion, which is closest to its heavy
citation type (pp. 109, 223), and Fedorovsk for variety — accented as the book accents (a breathing on an initial
vowel, an acute on one vowel, now and then a grave on a final one); then a separator (= , =, —, or an opening
bracket) and a stretch of real definition text in Old Standard, a few words in italics now and then. A quarter of
the heads are set in bold civil type instead, as the book sets its Russian headwords (Выбойка). The head words are
the GT's own headwords (ten pages) and the automatic heads, respelt the Church Slavonic way at random: у → ꙋ / ѹ /
оу, о → ѡ, я → ѧ / ꙗ, е → є / ѥ, и → ї before a vowel, ф → ѳ, кс → ѯ, пс → ѱ, от- → ѿ, and the rare letters (ѫ,
ѭ, ѩ, ѵ, ѕ, ꙁ) more often than real text has them, so that each is seen a few hundred times. Typst, not Python's
image library, sets them because only Typst positions the combining accents over their letters here. The rendering
is then cropped to its ink with the margin A's lines get, and roughened: ink and paper of random darkness, the ink
spread now and then, a rotation of up to half a degree, blur, noise. Checked against the real lines: 38 characters
a line against 36, a character's width relative to the line height 0.38 against 0.39.

*The experiment's question* is whether practice on these fonts carries over to the book's own types. Nothing but
the test will tell.

## 7. What building the data found

Pairing every GT line with scan A's line is also an audit of the GT, and it paid: comparing each GT line's length
with ABBYY's reading of the same line turned up 20 misplaced `¦` markers — a marker had been moved back over a
hyphen or dash (`съмрьтьни-¦полумертвы` became `¦съмрьтьни-полумертвы`) or to the start of a word the print had
broken (`Богоро¦дицы` became `¦Богородицы`) — and a second printed line missing from p. 109 (`(др. слав.
„искони“).`), hidden because a misplaced marker had made the line counts agree. `dj_inspect.py gtlines` now snaps a
marker over letters only, keeps a break deep inside a civil word, and reports every line whose length disagrees
with A's. It also showed a defect of the pipeline: the voted text of `Смокноути` (p. 623) is scrambled — D's words
out of order and a half line lost (PROGRESS.md).

## 8. Running it

    ~/.venvs/kraken/bin/ketos -d mps --workers 4 train -f path \
        -t djachenko/cache/hwocr/train.txt -e djachenko/cache/hwocr/val.txt \
        -o djachenko/cache/hwocr/model -B 16 --augment -q early

`-d mps` the Mac's GPU; `--workers 4` processes preparing (and augmenting) the images while the GPU trains;
`-f path` images with `.gt.txt` files; `-t`/`-e` the training and validation lists; `-o` the directory for the
checkpoints; `-B 16` the batch; `--augment` as in § 4; `-q early` stop when validation stops improving.

At the start Kraken (through PyTorch Lightning, the framework it trains with) prints a **model summary**: one row per
part — `val_cer` and `val_wer`, the scorers of the validation set (no parameters: they count, they do not learn),
`net` (the network) and `net.nn` (its stack of layers, the same numbers), an empty slot for extra layers, and
`net.criterion`, the CTC loss. On `net`: **Params 4.1 M** (the output layer grows with the alphabet); **Mode**
`train` (dropout active; reading switches it off); **In sizes** `[1, 1, 120, 400]`, the sample input Lightning
measures with — one line, one channel, 120 × 400 px; **Out sizes** `[1, 170, 1, 50]`, the scores it gives — 170
symbols (the 169 characters of the labels and the blank) in each of 50 frames (400 px ÷ 8: the three
`Mp2,2` poolings each halve the width, 2 × 2 × 2 = 8 — § 3); **FLOPs 1.6 B**, the
operations to read that 400-px line once. A real first line, scaled to 120 px high, is ~1,800 px wide, ~7 billion
operations, and training also works backwards through the network at about twice that again — some hundreds of
trillions an epoch, which is why the GPU sets the pace.

At the start Kraken also prints a warning like `alphabet mismatch: chars in training set only: {…} (not included in
accuracy test during training)`. It compares the characters of the training labels with those of the validation
labels; a character that never occurs among the 359 validation lines cannot be scored there, so it is left out of
`val_accuracy`. Expected for rare characters — Greek capitals, Latin letters of the etymologies, Cyrillic capitals,
`№`, `§` — and harmless. But the list is worth reading once: on the first run it also showed characters that
should not be in the labels at all (`{`, `■`, `|`, the look-alikes above), which is how the fold came about. Expect a
few hours — tens of epochs at ~12 minutes; `--resume <checkpoint>` continues an interrupted run. The progress bar
shows `train_loss` falling within each epoch and `val_accuracy` after it.

**Speed.** `--workers` is the number of processes that load, augment and batch the images while the GPU computes.
Measured during the first run (epoch 3): the four workers used 1.3 cores between them and the Mac was 61 % idle —
they wait for the GPU, which sets the pace (~11 min an epoch); more workers would not help. A larger batch
(`-B 32`) might: a GPU does 32 lines at once more efficiently than 16, at the price of half as many weight updates
an epoch — an experiment, to be judged by minutes an epoch and by the validation curve.

**The verdict**, on the test set only: `python3 tools/dj_hwocr.py eval` (~40 s; on the CPU, so it can run while the
GPU trains). It takes the best model in `cache/hwocr/model/` — the final `best_*.safetensors`, or while training
still runs its best checkpoint so far, converted — reads every line of the two test pages, and scores it as
`dj_eval.py` scores the vote: the model's line aligned with the GT's, a headword right when no edit touches it. The
question of § 1 — **does it read more of the 52 test headwords exactly than the vote does?** — is answered beside
the vote's reading of the same headwords, split by type (Church Slavonic, civil) and by whether scan A shows the
start of the line: on a column whose left margin the scan cuts off, the model sees headwords without their first
letters while the vote reads them in witness D. `cache/hwocr/eval/<model>/sheet.png` shows every test headword with
its image and the three readings; `report.tsv` has every line.

First look, the checkpoint after epoch 2 (val_accuracy 98.2 %), while training went on: on the sides scan A shows
whole, **31 of 40 headwords exactly right against the vote's 28**; on the cut column of p. 659, 2 of 12 against 8
(its images lack the letters). Where model and vote read a headword alike (27 times) they were right 26 times —
the independent-partner argument of § 1 in numbers.

Epoch 10 (val_accuracy 98.82 %, the run still going): **37 of 40 headwords right on the intact sides, the vote 29;
41 of 52 in all against 37**; the character error of the test lines 1.27 % (first lines) and 0.91 % (continuation
lines). The validation score had crept up by only 0.2 points since epoch 4, while the test headwords went from 30
to 37 of 40 — validation measures agreement with noisy automatic labels, mostly civil text; it is the right signal
for *when to stop*, not for *how good*. Where model and vote agreed (30 times) they were right every time. And the
model found two errors in the ground truth: on p. 246 it and the vote both read `Касфія`, `Катавасія` where the GT
had `…їа`; the scan shows ѧ (pointed, with a crossbar — the а of the same words is round). Corrected, and counted
fairly: two independent readers agreeing against the GT is the same test `dj_eval.py --suspects` applies to any pair
of readers — correcting the GT only where the model disagrees with it would tilt the test in the model's favour.
The three misses left on intact sides are all и/н in the citation type, which only the sense decides.

**The first run's end** (session 6): early stopping after epoch 22, the best epoch 12 (val_accuracy 98.92 %) kept as
`model/best_0.9892.safetensors`. On the test pages it reads as epoch 10 did: 37/40 headwords on the intact sides
(the vote 29), 41/52 in all (the vote 37), 30 of 30 right where it and the vote agree. The run had done what it
could; what moves the numbers now is the review answers, witness D's images for the cut columns, and the checked
test pages. A detail the sheet shows: on p. 246 the model reads
`священни` where the GT's label says `священни-` — the print broke the word without a hyphen, and the GT's
convention implies one; the model is right there.

Environment (session 6): `~/.venvs/kraken`, Kraken 7.1.1, PyTorch 2.14 with MPS. SciPy was upgraded to 1.17.1
there: the 1.15.3 that Kraken pins fails to load on macOS 27 (a compiled part the loader rejects), 1.17.1 loads,
and Kraken uses SciPy for image filtering, whose interface has not changed. `pip install scipy==1.15.3` undoes it.

## 9. The review round (active learning)

Making the 16,799 training labels perfect would take hundreds of hours and gain little: training averages scattered
label errors away — the model already reads more test headwords right than the vote its automatic labels came
from. What it lacks is *correct examples of the hard cases*, and those are exactly where it and the vote disagree.
Spending human effort on the cases a model finds hardest is called **active learning**:

1. `python3 tools/dj_hwocr.py book` — the model reads the first line of every entry of the book (~24,800; the images
   in `cache/hwocr/book/img/`, the readings in `cache/hwocr/book/readings.tsv`, each head beside the vote's).
   A trial on ten pages (leaves 100–109) with the epoch-5 checkpoint: model and vote read the head alike in 34 % of
   the lines scan A shows whole — and where they differ the model is mostly the one that is right: `Бѣдити` against
   the vote's `БКдити`, `Бѣдствовати` against `Бедсткокати`, `Бѣлыи` against `Καλωи` (the vote often reads ѣ as е or
   ъ). Its own weak spot shows too: В and К, alike in the headword type (`Квязати` for `Вказати`).
2. `python3 tools/dj_hwocr.py review --n 500` draws a sample of the disagreements — not on a GT page (their truth is
   known, and two are the test), not on a column whose left margin scan A cuts off — and writes sheets of 15:
   `cache/hwocr/review/NNN.png` shows each line's start, numbered, with the model's reading (a) and the vote's (b)
   under it; `djachenko/heads_review/NNN.txt` (committed — the user's work) has one line per number to answer:
   `a`, `b`, the headword itself if both are wrong (civil letters will do; letters as printed — `Апоплеѯіа` — are
   better, kept for stage 2 — `djachenko/CS_LETTERS.md` has every Church Slavonic letter and mark to copy, with ways to
   type them on the Mac), or `-` if the line begins no entry. **Only the headword counts**: everything before the
   separator (`=`, `—`, a bracket), several words if it has them (`Агіосъ надгробныи, Агіосъ задушныи`), not the text
   after it — that comes from the reader's own line (step 3). A displayed reading may run on past the headword
   (`a: Апоплезіа-греч`, a dash printed without spaces); `a` and `b` are judged by their headword part.
   Showing the two readings is faster than typing every word; its risk, *anchoring* (a plausible wrong suggestion
   is easier to accept than to invent), is small when the two disagree, since at least one is wrong. ~500 answers,
   about an hour.
3. `python3 tools/dj_hwocr.py data` adds every answered line as a fourth kind of sample, `checked`, labelled with the
   whole line as read by the reader whose head the user confirmed — the model's line for `a`, the vote's for `b`,
   and for a typed head the model's line with the typed head put over its own (matched with a free-end alignment,
   then to the end of the word). Not "the answered head, then the vote's line from its separator on": the two
   readers cut their heads at different places (`Апоплезіа-греч` against `Апоплазія-греч.-ударъ`), and a label
   must match its image exactly. Retrain, `eval`, and repeat while a round still pays.

   The first round (session 6), drawn from the epoch-10 model's reading of the whole book: 24,845 first lines; model
   and vote read the head alike in 49 % of the 22,142 lines scan A shows whole (14 % on the cut columns); 11,130
   disagreements to draw from, 500 drawn — sheets 001–034. Comparing two heads needed care: in norm text every dash
   is `-`, so a separator printed without spaces (`Агапы-греч.`) cannot be told from a hyphen inside a word; two
   heads count as alike when one is the other followed by `-`. The sample also turns up the pipeline's own faults:
   `0057-1-16`, where the scan's line reads `встрѣтившееся…` and the vote puts `Аполинъ` — answered `-`.

The answers are also proofread headwords, which a corrections layer can later give to the edition itself.

## 10. What comes after

If stage 1 beats the vote on the test pages: **stage 2**, letters as printed — the target (the user, session 6: not
"plain Russian"; whether the titla and accents are recorded too is left open, so nothing may rule them out). Stage 1 does not lock this out: the images keep every letter, the
strict labels are kept (GT, synthetic, the user's typed answers), and entries.tsv holds the printed form and the civil
one apart. A civil reading cannot be turned back — у may be у, ꙋ, ѹ, оу or ѫ — but a *confirmed* one narrows a
headword to a handful of spellings (`Азбука`: Азбука, Азбꙋка, Азбѹка, Азбоука), and choosing among them is a far
smaller task than reading: the stage-1 model trained on with the Church Slavonic letters added to its alphabet,
then made to score the candidate spellings of every confirmed headword (*constrained reading*), orthographic rules
as tie-breakers, the confident choices as new labels (*self-training*), review rounds in printed letters; **stage 3** perhaps the accents; and **self-training** —
the model reads every headword of the book, readings that agree with D or B join the training data, train again.
The 242 pages whose left margin scan A cuts off need witness D's images of the same lines. The heavy citation type
will stay hard for any glyph model — in it и and н are one glyph, which only the sense decides; there (A) or the
proofreader has the advantage. Whatever the outcome, the model's readings are one more independent witness for
the vote.

## Glossary

- **CER** — character error rate: the edits (insertions, deletions, substitutions) needed to turn the reading into
  the truth, divided by the length of the truth. Kraken's *accuracy* is 1 − CER.
- **checkpoint** — the network's weights saved at one moment of training.
- **codec** — the alphabet the network can output, built from the training labels.
- **convolution** — a small learned pattern detector applied everywhere across the image.
- **CTC** — the scheme that lets a network learn to read lines from (image, text) pairs without letter positions.
- **dropout** — switching off a random part of the network during training, against memorising.
- **epoch** — one pass over all training lines; **batch** — the lines processed together for one update.
- **label noise** — wrong labels in the training data; tolerable in small measure.
- **leakage** — test data finding its way into training; it flatters the test.
- **LSTM** — a recurrent layer that reads a sequence and carries context along it.
- **overfitting** — learning the training examples instead of the rule.
- **synthetic data** — training examples made rather than found; the *domain gap* is how far they differ from the
  real ones.
