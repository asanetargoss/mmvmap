# mmvmap - MCP Mapping Viewer Mapper

A small command line utility for making a human-readable version of a decompiled Minecraft mod.

**Prerequisites**
- Python 3.5+
- A Java decompiler ([jd-gui](http://jd.benow.ca/#jd-gui) for ease-of-use, [fernflower](https://github.com/fesh0r/fernflower) for reliability)

**Soft Prerequisites (for basic usage):**
- [MCP Mapping Viewer](https://github.com/bspkrs/MCPMappingViewer/)
- The mod is for Minecraft 1.7.10+ (or whatever version MCP Mapping Viewer feels like supporting in the future)

**Basic usage:**

1. Decompile the mod
2. Run MCP Mapping Viewer and select the latest mapping for your desired version. This will populate the cache.
3. From command line: ```python mmvmap.py [decompiled-mod-folder] -mmv```

The remapped mod source will be a copy, leaving the original untouched.

## Advanced Use

mmvmap, when used with the -mmv flag, piggybacks off the MCP Mapping Viewer cache's folder structure. You can instead specify a custom folder containing the mapping files (fields.csv, methods.csv, params.csv), where the first column contains searge names and the second column contains mcp names. For a full list of usage options, use the ```--help``` flag:

```python mmvmap.py --help```

## See Also

- [MinecraftRemapping](https://github.com/agaricusb/MinecraftRemapping) - Another mapping tool. Also has mappings for older Minecraft versions, in another format.