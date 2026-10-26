# Simple Voice Chat (NeoForge 1.21.1)

## 9306988

Fixed failing to join a group while in another group desyncing the clients state

Fixed group desync when joining a group that was destroyed before joining it

Fixed invites with passwords that contained backslashes or quotes not working

Instantly disconnect the client on a packet parsing error instead of timing out

Don't stop processing when receiving an invalid UDP packet on the client

Fixed API returning a nonexistent group as non-null

Fixed audio player not being stopped in some cases

Fixed removing audio senders not returning if the actual audio sender has been removed

Fixed keybinds not applied properly from the voice chat settings screen

Fixed potential race when opening to LAN

## 8928478

Ignorevoice_hostin singleplayer and LAN worlds

Improved sound manager error messages

Added Thai translation

## 8807853

Fixed JoinGroupEvent being fired for wrong password attempts

Fixed error when shutting down a server

Improved resiliency against mods that change the camera off-thread

## 8601207

Fixed some speakers breaking voice chat audio

Fixed race condition when quickly disconnecting and reconnecting

Fixed voice chat breaking if Minecrafts audio system is not initialized

Fixed potential OpenAL resource leaks

Fixed incorrect OpenAL version detection
