**Estimated time:** 75 minutes. **Competencies:** prompt engineering, creativity and innovation.

{{video:m1-l1}}
{{youtube:lnE1iTkWluk | Introduction: Music Lesson One}}

## Learning objectives

By the end of this lesson you will be able to:

1. Write a structured song prompt that specifies genre, tempo, mood, instrumentation, vocal style, and form.
2. Generate at least three versions of a song from your own lyrics and select one using musical criteria.
3. Explain, in a 75-word rationale, which prompt choices produced the strongest result and why.

## Warm-up: listen like a producer (5 minutes)

Play any recorded song you know well. While it plays, write down six things a producer had to decide: tempo, key or mode, instrumentation, vocal style, form (verse, chorus, bridge), and mood. These six decisions are exactly what a text-to-song model needs from you. If you leave them out, the model decides for you.

## Key ideas

### A prompt is a brief, not a wish

Text-to-song tools such as Suno take two inputs: a **style prompt** (a short description of how the song should sound) and **lyrics** (the words, with structure tags such as [Verse] and [Chorus]). Vague prompts ("a nice pop song") produce generic output. Specific prompts ("upbeat indie pop, 118 BPM, bright acoustic guitar and handclaps, warm female alto vocal, sparse first verse building to a full chorus") give the model constraints to work within, and constraints are where style lives.

### The five-part prompt frame

Use this frame for every music prompt in the course:

| Part | Question it answers | Example |
| --- | --- | --- |
| Genre and era | What tradition does this belong to? | "1970s soul ballad" |
| Tempo and feel | How fast, and how does it move? | "slow, around 68 BPM, laid-back swing" |
| Instrumentation | What do we hear? | "Rhodes piano, upright bass, brushed drums, string pad" |
| Vocal | Who sings, and how? | "husky tenor, intimate, close-mic" |
| Arc and mood | How does it change over time, and how should it feel? | "starts hushed, opens up at the second chorus, bittersweet" |

### Structure tags do the sequencing

Lyrics with tags such as [Intro], [Verse 1], [Pre-Chorus], [Chorus], [Bridge], and [Outro] tell the model where sections begin. Without them, choruses land in strange places. Tags are your first taste of computational thinking: you are sequencing the form so the model can follow it.

### Iterate on purpose

Generation is cheap; judgment is not. Change **one variable** per generation so you can hear what it did. A useful order: get the form right first, then the tempo and feel, then the instrumentation, and finally the vocal.

## Activity: compose your song (45 minutes)

1. **Write lyrics** for a short song: two verses and a chorus, optionally a bridge. Keep it under 16 lines. Choose a topic connected to teaching, your community, or a piece you already love. Write in your own words; do not ask a text model to write the lyrics for this lesson.
2. **Tag the structure** with [Verse 1], [Chorus], [Verse 2], [Chorus], [Bridge], [Chorus].
3. **Write a style prompt** using the five-part frame. Keep it under 200 characters if the tool limits length.
4. **Generate version 1** in Suno with custom mode on, pasting your lyrics and style prompt.
5. **Listen critically.** Fill in the evaluation grid below.
6. **Change one variable** and generate version 2. Repeat for version 3. Record what you changed each time in your Music Module Notes.
7. **Select** the strongest version. Download it as MP3 and name it `Lesson-1-1_LastName_Title.mp3`.

### Evaluation grid

| Criterion | Version 1 | Version 2 | Version 3 |
| --- | --- | --- | --- |
| Form follows my tags | | | |
| Tempo and feel match the brief | | | |
| Instrumentation matches the brief | | | |
| Vocal phrasing is natural and intelligible | | | |
| Lyrics are sung as written | | | |
| Overall: would I play this for a class? | | | |

### Prompt bank

Adapt any of these as starting points:

- "Gospel-influenced pop, 96 BPM, piano and choir, powerful female lead, builds to a big final chorus, hopeful"
- "Lo-fi hip hop, 82 BPM, dusty drums and vinyl crackle, soft male spoken-sung vocal, mellow and reflective"
- "Afrobeats, 104 BPM, log drum and shaker, bright synth chords, playful call-and-response vocals, celebratory"
- "Folk ballad, 3/4 time, fingerpicked guitar and cello, gentle alto, wistful, ends quietly"

## Create and share

Post in the **Lesson 1.1 Gallery**:

- Your selected MP3 or a share link.
- Your final lyrics with tags.
- Your final style prompt.
- A rationale of no more than 75 words: which prompt choices produced the strongest result and why.
- Your one-line AI credit (see "Using AI Responsibly").

## Resources

- Suno help center: how custom mode and structure tags work.
- Any recording you used in the warm-up, as a reference for arrangement.
- Optional: Boomy or Udio, if Suno is unavailable on your network.

## Reflection prompts

Answer in your Music Module Notes; you will draw on them for the module reflection.

1. Which of the five prompt parts made the biggest audible difference?
2. Where did the tool ignore your instructions, and how did you respond?
3. If a student handed you this song, what feedback would you give on the lyrics versus the production?
