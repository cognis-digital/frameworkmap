"""FRAMEWORKMAP MCP server — exposes scan() as an MCP tool for Cognis.Studio."""
from __future__ import annotations
from frameworkmap.core import scan, to_json

def serve() -> int:
    """Start an MCP stdio server. Requires the optional 'mcp' extra:
        pip install "cognis-frameworkmap[mcp]"
    """
    try:
        from mcp.server.fastmcp import FastMCP
    except Exception:
        print("Install the MCP extra: pip install 'cognis-frameworkmap[mcp]'")
        return 1
    app = FastMCP("frameworkmap")

    @app.tool()
    def frameworkmap_scan(target: str) -> str:
        """Crosswalk controls across NIST, ISO 27001, SOC 2, CMMC, PCI. Returns JSON findings."""
        return to_json(scan(target))

    app.run()
    return 0
