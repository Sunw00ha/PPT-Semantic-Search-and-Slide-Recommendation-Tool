# PPT Recommendation System - Desktop App

A simple desktop application for the PowerPoint slide recommendation system.

## Features

### File Management
- **View embedded files**: See all PowerPoint files that have been processed
- **Add new files**: Drag & drop or browse to add PowerPoint files
- **Refresh files**: Reprocess files if they've been modified
- **Remove files**: Delete specific files from the embedding database
- **Clear all**: Remove all embeddings (with confirmation)

### Recommendations
- **Select file**: Choose any PowerPoint file for analysis
- **Enter slide number**: Specify which slide to analyze
- **Get recommendations**: Find similar slides from your embedded collection
- **View results**: See similarity scores and content previews

## Quick Start

1. **Activate virtual environment**:
   ```bash
   source PPTenv/bin/activate
   ```

2. **Start the desktop app**:
   ```bash
   python3 run_app.py
   ```

3. **Use the menu**:
   Follow the on-screen menu to manage files and get recommendations

## How It Works

1. **Add Files**: Upload PowerPoint files to create embeddings
2. **Get Recommendations**: Select any PowerPoint file and slide number
3. **View Results**: See similar slides ranked by similarity score

## API Endpoints

The web UI communicates with a Flask API server:

- `GET /api/files` - List embedded files
- `POST /api/add-files` - Add new files
- `POST /api/recommendations` - Get recommendations
- `POST /api/refresh-all` - Refresh all files
- `POST /api/clear-all` - Clear all embeddings

## File Structure

```
PPTtool/
├── ui.html              # Web interface
├── api_server.py        # Flask API server
├── start_ui.py         # Startup script
├── src/
│   ├── vector_database.py
│   └── ppt_manager.py
└── test_ppts/          # PowerPoint files
```

## Troubleshooting

- **Port 5000 in use**: The server uses port 5000 by default
- **Files not loading**: Check that PowerPoint files are in the correct format (.pptx)
- **No recommendations**: Make sure you have embedded files first
- **Virtual environment**: Ensure PPTenv is activated before starting

## Next Steps

This is Step 1 of the UI development. Future enhancements could include:
- Slide preview thumbnails
- Batch file operations
- Advanced search filters
- Export recommendations
- PowerPoint integration
