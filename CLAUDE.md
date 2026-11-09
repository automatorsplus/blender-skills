# Blender Skills Project

Blender Skills Pack for Cursor and Claude Code with Blender MCP integration.

## Project Structure

```
.claude-plugin/          # plugin.json + marketplace.json
.claude/skills/          # 99 specialist skills + shared references
.cursor/mcp.json         # Blender MCP (Cursor)
.mcp.json                # Blender MCP (Claude Code)
docs/BLENDER_MCP_SETUP.md
```

## Agent Instructions

1. For Blender asset tasks, read **blender-director** first for complex work
2. **If user attaches a reference image:** read `references/reference-image-match.md` and complete Reference Analysis before MCP execution
3. **Check Blender MCP** — if connected, execute via MCP; never narrate UI steps. **If it is not connected,
   use `headless-render`**: build the scene as a Python script and render with Blender in the background. Never
   stop to ask the user to install the MCP, and never narrate UI steps instead
4. **Before any render over a minute, use `preview-first`**: six preview stills, a contact sheet, a time estimate
5. Read MCP tool schemas before calling (see `references/mcp-tools.md`)
6. Follow universal pipeline in `references/asset-pipeline.md`
7. Validate before export using `references/validation-checklist.md`
8. For reference tasks, also run `references/visual-match-checklist.md`
9. Use naming conventions from `references/naming-conventions.md`

## MCP Setup

Optional. For live work in the Blender window, Blender must be running with the BlenderMCP addon connected
(`docs/BLENDER_MCP_SETUP.md`). For finished renders it is not needed: `headless-render` only needs Blender installed.

## Key Files

- `QUICKSTART.md` — Installation
- `SKILLS_GUIDE.md` — Decision trees and workflows
- `README.md` — Overview
