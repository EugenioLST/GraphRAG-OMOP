# GraphRAG-OMOP Frontend Dashboard

Professional web interface for clinical text standardization to OMOP concepts.

## Quick Start

```bash
npm install
npm run dev
# Open http://localhost:3000
```

**Backend must be running on port 8000!**

## Features

- ✅ Backend status monitoring with real-time polling
- ✅ Clinical text input with 3 pre-loaded examples
- ✅ Two-stage processing (Extraction → OMOP Mapping)
- ✅ Interactive results table with sorting & filtering
- ✅ CSV export with timestamp
- ✅ Keyboard shortcuts: `Ctrl+Enter` to process, `Esc` to clear
- ✅ Responsive design for all devices
- ✅ Professional medical-grade UI with shadcn/ui

## Tech Stack

- **Next.js 16** with App Router
- **TypeScript** for type safety
- **Tailwind CSS 4** for styling
- **shadcn/ui** components
- **Lucide React** icons

## Complete Setup Guide

See [`../DASHBOARD_QUICKSTART.md`](../DASHBOARD_QUICKSTART.md) for detailed instructions.

## Development

```bash
# Install dependencies
npm install

# Run dev server
npm run dev

# Build for production
npm run build

# Start production server
npm start
```
