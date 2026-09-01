# Distant Horizons (NeoForge 1.21.1)

## 8389148

Highlights:

Add LOD Textures
Only available for base DH rendering, Iris shaders will render LODs as untextured (this would need to be fixed on Iris' end)

Increase LOD quality when zoomed in
When zoomed in on distant LODs they will slowly increase in quality, increasing your CPU load will improve the loading speed.

Increase the minimum required OpenGL version 3.2 -> 3.3
Done to fix AMD generic (cloud/beacon) rendering

When using the "Auto" rendering engine, Iris will no longer cause the game to crash

Fix a ByteBuffer memory leak

Full Changelog

Additions:

Add LOD Textures
Only available for base DH rendering, Iris shaders will render LODs as untextured (this would need to be fixed on Iris' end)

Increase LOD quality when zoomed in
When zoomed in on distant LODs they will slowly increase in quality, increasing your CPU load will improve the loading speed.

Add a warning if explicit GC is disabled
Disabling explicit GC is known to cause memory leaks

Add a warning if OpenGL is used on MC 26.2

Improvements:

F3 pooled arrays show total bytes

ByteBuffer pooling

Pool ByteBuffers on LOD loading

Pool IBO cpu buffers

Reduce far plane clipping on LOD only mode

Several minor garbage collection pressure reductions

Changes:

When using the "Auto" rendering engine, Iris will no longer cause the game to crash
Formerly this would cause the game to crash

If DH is set to explicitly use Blaze3D the game will still crash due to Iris not supporting Blaze3D

Increase the minimum required OpenGL version 3.2 -> 3.3
Done to fix AMD generic (cloud/beacon) rendering

Bug Fixes:

Fix replay of waiting client chunks after server level keying

Fix instanced rendering not working on AMD

Fix auto updater looking for the wrong 26.2 version

Fix GL using the last frame's viewport size (fixes Vista camera rendering)

Fix memory leak on GL viewport size change

Fix 1.12.2 self updater crash

Fix 1.12.2 GL states for vanilla

Fix 1.12.2 VBO binding leaks

Fix 1.12.2 beacon tint color using a client-only method

Fix a rare null pointer in Blaze terrain rendering

Fix Immersive Portals mixin warning when Immersive Portals isn't present
## 8037637

_Changelog will be populated by the CurseForge registry updater._
