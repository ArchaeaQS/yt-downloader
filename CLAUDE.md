# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Language Setting

**IMPORTANT**: Always respond in Japanese (日本語) when working with this codebase. This is a Japanese application and the development team communicates in Japanese.

## Project Overview

This is a Japanese YouTube downloader desktop application built with Python and Tkinter. It downloads YouTube videos in MP4 format with selectable quality options and supports membership-restricted videos via cookie authentication.

## Architecture

### Core Components

- **yt_downloader.py**: Main application entry point containing:
  - `YouTubeDownloader`: Main application class managing download logic and async operations
  - `YouTubeDownloaderUI`: UI management class handling Tkinter interface components
  - `DownloadState`: State manager for download operations
  - `UIState`: State manager for UI variables

- **tool_manager.py**: External tool management system that automatically downloads and manages:
  - ffmpeg.exe (video processing)
  - yt-dlp.exe (YouTube downloading)
  - AtomicParsley.exe (metadata embedding)

- **config.py**: Configuration constants for video quality options

### Key Architecture Patterns

- **Separation of Concerns**: UI logic is separated from download logic and tool management
- **Async/Threading**: Uses asyncio loop in separate thread for non-blocking downloads
- **State Management**: Dedicated classes for managing download and UI state
- **Auto-dependency Management**: Tools are automatically downloaded to user's AppData directory

### Cookie System

The application supports two cookie modes:
1. Manual cookie input via dialog (stored in `%USERPROFILE%\AppData\Local\yt-downloader\cookies.txt`)
2. Automatic Firefox browser cookie extraction using `--cookies-from-browser firefox`

## Development Commands

### Building Executable
```bash
pyinstaller yt_downloader.spec
```

### Running Application
```bash
python yt_downloader.py
```

### Tool Installation
Tools are automatically downloaded to: `%USERPROFILE%\AppData\Local\yt-downloader\tools\`

## Key Implementation Details

- Downloads use yt-dlp with format: `bestvideo[height<={quality}][ext=mp4]+bestaudio[ext=m4a]/best`
- Progress tracking is implemented but currently incomplete (TODO comments in code)
- Stop functionality is partially implemented with cancellation support
- Cookie file permissions are set to user-only (0o600) for security
- Thumbnail embedding and metadata processing via AtomicParsley

## Common Issues

- Progress bar updates need completion (yt_downloader.py:328, 201)
- Download stopping mechanism needs refinement
- No requirements.txt or dependency management file exists - dependencies must be inferred from imports

## Dependencies (Inferred from Code)

- tkinter (built-in)
- asyncio (built-in) 
- requests
- pathlib (built-in)
- subprocess (built-in)

External tools (auto-downloaded):
- yt-dlp
- ffmpeg
- AtomicParsley