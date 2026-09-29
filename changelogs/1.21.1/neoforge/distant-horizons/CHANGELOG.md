# Distant Horizons (NeoForge 1.21.1)

## 9004764

Highlights:

Fix Iris on MC 26.1.2 and newer having rendering issues (most noticeable with Bliss shaders)
Fix Iris 26.1.2+ not having access to DH's lightmap

Fix Iris 26.1.2+ having incorrect blend

Only disable DH world gen when Chunky world gen is also active

Up config version 4 -> 5
This will clear your config

This is necessary to fix an issue where some users are missing necessary config values related to grass textures

Full Changelog

Changes:

Allow 1.12.2 to run with just Mixinbooter instead of Cleanroom

Only disable DH world gen when Chunky world gen is active
This feature is only available for MC versions 1.19.2 and newer due to Chunky not providing the necessary API for older MC versions

Up config version 4 -> 5
This will clear your config

This is necessary to fix an issue where some users are missing necessary config values related to grass textures

Ignore DB shutdown errors in update propagator

Start LWJGL 2/3 separation for future MC 1.7.10 support
This shouldn't affect anything, if you notice any rendering issues please report them

rate limit chunk read deserializing error logging

Bug Fixes:

Fix the chat world gen progress getting out of sync

Fix singleplayer server references not closing

Fix Karnatour not being included in the author list

Fix an extremely rare GL crash if your GPU doesn't support GL 4.3 or vertex attribute binding

Fix a rare neoforge lightmap wrapper crash

Fix Iris not getting DH's bound lightmap on some versions

Fix 26.3 world gen sometimes hanging the server thread on shutdown

Fix LOD holes and LODs not generating for CLIENT_ONLY for 1.12.2

Fix DH setting the blend state incorrectly for MC 26.1.2+
## 8943824

Highlights:

Up API version 7.1.0 -> 7.2.0

Mark SSRD (Separate Sable Render Distance) 1.8.6 and below as incompatible
Due to DH's change to rendering with Reverse Z depth, SSRD must update, otherwise incorrect rendering will occur

Improve server thread health check logic

Improve Iris support for MC 26.3
Some fixes may still be necessary on Iris' end as of Iris 1.11.6

Full Changelog

Additions:

Up API version 7.1.0 -> 7.2.0

When a config value is being controlled by the API, API users can now provide their mod's name to show who is actively controlling that option
for old API users this value will appear as "UNKOWN" and a warning will be logged

Add the same Iris frame buffer depth fix to Oculus for MC 1.20.1

Add server thread healthy check for dedicated servers on MC 1.12.2

Improvements:

Improve Iris support for MC 26.3
Some fixes may still be necessary on Iris' end as of Iris 1.11.6

Changes:

Disable chunk regeneration if the chunk gen mode is Pre-existing and the gen plan is surface_only

Mark SSRD (Separate Sable Render Distance) 1.8.6 and below as incompatible
Due to DH's change to rendering with Reverse Z depth, SSRD must update, otherwise incorrect rendering will occur

Increase the server healthy time from 10 -> 25 milliseconds (half of a healthy server tick)
and increase the 99th percentile timeout to 50 milliseconds

This should fix some issues where the server healthy check completely prevented world gen from running

Capture and restore blending/depth mask GL state on MC 1.12.2

Bug Fixes:

Fix the surface generator putting oceans in The End for some MC versions

Fix vanilla fading using DH's depth range instead of MC's

Prevent zooming on extremely low detail LODs causing holes

Fix CleanMix and Gregtech bloom leaking through opaque blocks in 1.12.2

Fix server not applying unsupported configs

Fix Neoforge crashing on MC 26.3 if Blaze3D rendering is enabled

Fix Forge mixin plugin not running

Fix 1.12.2 holes when playing on a dedicated server

Fix crash when iris fork and Gregtech is present on 1.12.2

Fix DH disappearing when a glow is on screen for MC 26.3

Fix 1.12.2 failing to apply Mixins if an old version of Cleanroom is used

## 8908517

Bug Fixes:

Fix Neoforge config options not using lang names

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
