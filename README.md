# 🩺 Healthcare AI Research Agent

An AI research assistant for healthcare. It finds real medical papers, summarizes them
in the **PICO** format that medical researchers use, compares them, suggests research gaps,
and then **checks each gap against real research** before trusting it.

Built with **Python**, **Streamlit**, **Amazon Bedrock** (Converse API) and the **OpenAlex** API.

<!-- Screenshots: save images in docs/images/ and uncomment the line below.
![The app](docs/images/app.png)
-->

---

## ✨ What makes it different

Most AI research tools simply trust the AI. This one **tests the AI's claims with real data**.

| Feature | What it does |
|---|---|
| 🏥 **Healthcare only** | Searches only health fields (Medicine, Nursing, Pharmacology, Dentistry, Health Professions) and only papers with an abstract |
| 📋 **PICO summaries** | Study type, **P**atients, **I**ntervention, **C**omparison, **O**utcome and Limitations, grounded in the abstract only |
| ⚖️ **Comparison** | Common findings, differences and research gaps, with paper numbers like [1] so every claim can be traced |
| 🔎 **Gap checker** | The AI suggests gaps **and** a search for each one. The app counts matching papers in OpenAlex and labels each gap: 🟢 likely a real gap · 🟡 partly studied · 🔴 already well studied |
| 📄 **Report with real references** | One downloadable report. References come from OpenAlex, **never from the AI**, so they can't be invented |

---

## 🧠 How it works

```
            ┌──► OpenAlex 📚        find papers, count papers for each gap  (free)
  app.py  ──┤
(Streamlit) └──► Amazon Bedrock 🧠  summarize, compare, suggest gaps        (pay per use)
```

1. **Search**: OpenAlex returns healthcare papers on your topic.
2. **Summarize** (on click): Bedrock writes a PICO summary from the abstract.
3. **Compare**: Bedrock compares the summarized papers.
4. **Check gaps**: Bedrock suggests 3 gaps with search queries, then the app counts papers
   for each query in titles and abstracts, and gives a verdict.
5. **Report**: Python puts everything together with a reference list. No AI, so it's free.

The full study guide, with every file explained, is in [docs/HOW_IT_WORKS.md](docs/HOW_IT_WORKS.md).

---

## 🛠️ Tech stack

| Part | Tool |
|---|---|
| Web interface | Streamlit |
| AI model | Mistral Large 3 on **Amazon Bedrock**, through the **Converse API** (boto3) |
| Research data | **OpenAlex** API (250+ million papers) |
| Language | Python (dataclasses, type hints) |

---

## 🛡️ Safety, cost and quality

- **Grounded prompts:** the AI may only use the title and abstract, and writes
  "Not stated in the abstract." instead of guessing.
- **Prompt-injection defence:** paper text goes inside `<paper>` tags, with an instruction not to follow anything inside them.
- **Validated output:** every AI answer is checked (headings or JSON) and retried once if it's incomplete.
- **Real references only:** reference lists are built from OpenAlex data, not written by the AI.
- **Cost control:** the AI runs only when you click, summaries are cached so the same paper is never paid for twice,
  answers have a token limit, and comparisons use short summaries instead of full abstracts.
- **Secrets stay out of the code:** AWS keys live in `~/.aws`, and settings live in `.env` (never uploaded).

> ⚠️ This is a tool for studying research, **not medical advice**. AI summaries can contain
> mistakes, so always check the original paper.

---

## 🚀 Setup (Windows)

**You need:** Python 3.12 or newer, an AWS account with Amazon Bedrock access, and a free
[OpenAlex API key](https://openalex.org/settings/api-key).

1. Create a virtual environment and install the packages:

   ```
   python -m venv .venv
   .venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   ```

2. Create your settings file, then add your OpenAlex key to it:

   ```
   copy .env.example .env
   ```

3. In the AWS Console, open **Amazon Bedrock** and make sure the model in `.env` is available
   in your region. Create an IAM user that is allowed to call Bedrock, then save its access key
   on your computer (never in this project):

   ```
   aws configure
   ```

4. Start the app (or double-click `start_app.bat`):

   ```
   streamlit run app.py
   ```

---

## 📁 Project structure

```
app.py                  The web page (Streamlit)
config/settings.py      Reads settings from .env
src/models.py           The Paper data class
src/openalex_client.py  Searches and counts healthcare papers in OpenAlex
src/bedrock_client.py   The only file that talks to the AI (Bedrock Converse API)
src/prompts.py          All the instructions given to the AI
src/summarizer.py       PICO summary of one paper
src/analyzer.py         Compares papers
src/gap_checker.py      Suggests gaps with AI, then checks them in OpenAlex
src/report.py           Builds the downloadable report with references
.streamlit/config.toml  The app's colours and theme
docs/HOW_IT_WORKS.md    Full study guide
```

---

## ✅ Progress

- [x] Search healthcare papers with OpenAlex
- [x] Connect to Amazon Bedrock
- [x] PICO summaries
- [x] Compare papers
- [x] Gap checker verified against OpenAlex
- [x] Research report with real references
- [x] Modern interface (theme, tabs, cards)
- [ ] Real agent with tool use (the AI decides when to search)
- [ ] Automated tests
- [ ] Deploy online

---

## ⚖️ Known limitations

- Summaries use the **abstract only**, not the full paper.
- Gap counts are a **strong hint, not proof**: papers that use different words can be missed,
  and the 🟢/🟡/🔴 thresholds (10 and 50 papers) are a first estimate.
- It's an **AI pipeline with one agent-like step** (the AI writes its own searches), not yet a full agent.
