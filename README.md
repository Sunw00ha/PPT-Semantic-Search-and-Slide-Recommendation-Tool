# PPTtool

Local desktop tool that indexes PowerPoint (`.pptx`) slides semantically and helps you find or reuse slides from presentations you already have.

For each slide, the pipeline extracts on-slide text and images, generates image captions, optionally summarizes very long text, builds embeddings, and stores them in a local vector database for search and slide recommendations.

## Features

- **Semantic indexing** — slide-level embeddings (text + image captions)
- **Search** — find slides by meaning, not just exact keywords
- **Recommendations** — given a deck and slide number, surface similar slides from other indexed decks
- **Desktop GUI** — add files, refresh the index, search, and get recommendations

## How it works

```
.pptx  →  extract text + images  →  BLIP-2 captions  →  (optional) DistilBART summary
       →  combine per slide  →  embed  →  ChromaDB  →  search / recommend
```

- **Text:** `python-pptx`
- **Image captions:** BLIP-2 (`Salesforce/blip2-opt-2.7b`)
- **Summarization:** DistilBART (`sshleifer/distilbart-cnn-12-6`) for slides over ~150 words
- **Embeddings & storage:** ChromaDB + `sentence-transformers` (`all-MiniLM-L6-v2`)

## Requirements

- Python 3.9+ (3.10+ recommended)
- macOS, Linux, or Windows
- **Disk:** several GB free (PyTorch + model weights on first run)
- **RAM:** 8 GB minimum; 16 GB+ recommended for BLIP-2
- **GPU:** optional but speeds up image captioning
- **Tkinter** for the GUI (often bundled with Python; on some Linux installs you may need `python3-tk`)

## Installation

From the project root:

```bash
python3 -m venv PPTenv
source PPTenv/bin/activate   # Windows: PPTenv\Scripts\activate

pip install -r requirements.txt
```

The first time you index a file with images, Hugging Face will download BLIP-2 and DistilBART weights. This can take a while.

## Quick start (GUI)

Recommended way to use the project:

```bash
source PPTenv/bin/activate
python3 run_gui.py
```

In the app:

1. **File Management** — add `.pptx` files (processing runs the full pipeline and stores embeddings).
2. **Recommendations** — pick a file and slide number to find similar slides from other decks.
3. **Search** — query the indexed slides by text.
4. **Statistics** — view how many slides/decks are indexed.

Indexed data is stored locally under `ppt_embeddings_db/` (created automatically; not meant to be committed).

## Command-line usage

Run pipeline scripts from the `src/` directory so imports resolve correctly:

```bash
cd src
```

### Text extraction

```bash
python extract_text.py ../test_ppts/image_testing/animals.pptx
```

### Image captioning (BLIP-2)

```bash
python image_captioning_pipeline_blip2.py ../test_ppts/image_testing/animals.pptx
```

### Full combine pipeline (text + captions + summarization)

```bash
python combine_data.py ../test_ppts/combine_data_test/DStest2.pptx
```

### Interactive manager (index, search, recommend)

```bash
python ppt_manager.py interactive
```

Other commands:

```bash
python ppt_manager.py add ../test_ppts/recommend_test/testOnlyWEATHER.pptx
python ppt_manager.py search "weather forecast"
python ppt_manager.py recommend ../test_ppts/recommend_test/testOnlyWEATHER.pptx 3
python ppt_manager.py stats
```

## Project structure

```
PPTtool/
├── README.md
├── requirements.txt
├── run_gui.py              # Start the desktop app (run from repo root)
├── gui_app.py              # Tkinter UI
├── simple_text_search.py   # Lightweight text-only search (no ML)
├── src/
│   ├── extract_text.py
│   ├── extract_images.py
│   ├── caption_images_blip2.py
│   ├── image_captioning_pipeline_blip2.py
│   ├── combine_data.py           # merge + summarization
│   ├── generate_embeddings.py    # standalone embedding helper
│   ├── vector_database.py        # ChromaDB index, search, recommendations
│   └── ppt_manager.py            # CLI wrapper
└── test_ppts/              # sample decks for trying the tool
```

## Sample test files

Example paths under `test_ppts/`:

- `image_testing/animals.pptx`
- `combine_data_test/DStest2.pptx`
- `recommend_test/testOnlyWEATHER.pptx`

Add your own `.pptx` files via the GUI or `ppt_manager.py add`.

## Troubleshooting

| Issue | What to try |
|-------|-------------|
| `ModuleNotFoundError` for `extract_text`, etc. | Run scripts from `src/` as shown above, or use the GUI from the repo root. |
| GUI does not open | Ensure Tkinter is installed (`python -m tkinter` should open a small window). |
| Very slow first index | Expected: BLIP-2 download + captioning every image. Use a machine with GPU if possible. |
| Out of memory | Close other apps; try smaller decks first; CPU + BLIP-2 is memory-heavy. |
| No recommendations | Index at least two different decks first; recommendations exclude slides from the same file. |

## Notes

- Only **`.pptx`** files are supported (`.ppt`).
- Re-processing: the GUI **Refresh** button (or `ppt_manager.py` with force refresh) re-runs the pipeline when files change.
- `ppt_embeddings_db/` and local JSON caches are gitignored.
