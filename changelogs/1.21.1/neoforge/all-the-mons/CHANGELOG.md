# All the Mons (NeoForge 1.21.1)

## 8822048

[Detailed changelog](https://github.com/AllTheMods/All-the-Mons/blob/main/CHANGELOG.md)

Changelog

I would walk 500 chunks
And I would walk 500 more
Just to get the cosmic dust I need
To spawn a Cosmog at my door

1.3.0 is a fix-focused release.Cosmic Dustnow actually generates in the End at a decent rate, soCosmogis obtainable without an unreasonable amount of exploring, andReliquified Artifactsitems no longer equip into Accessories slots where they did nothing. A batch of long-standing recipe conflicts is resolved, the compasses stop listing content the pack does not generate, and the coremod brings a large pasture performance win.

NeoForge updated to 21.1.249.

Pack changes

Fixed Cosmic Dust barely generating in the End, which made Cosmog effectively unobtainable (LobsterJonn)

Stopped Reliquified Artifacts items equipping into Accessories slots, where they did nothing (LobsterJonn)

Big pasture performance improvement, a pasture no longer scans the owner's entire PC twice every tick (LobsterJonn)

Pokémon species names are no longer rebuilt with a regex every time they are read, which was most of the cost of CobbleWorkers jobs (LobsterJonn)

Fixed a dupe where automation could pull the in-progress result out of a Cobblefurnies stove or cooking pot (LobsterJonn)

Fixed a crash when scanning chunks containing a Cobblemon Gilded Chest (LobsterJonn)

Fixed duplication when using Apokinetics Precision and Yielding gems on compression recipes (LobsterJonn)

Fixed a memory leak in the recipe event (#720) (Uncandango)

Dropped the Legendary Monuments Azure Flute and Ingredient mixin workarounds, fixed in LM 8.1 update (LobsterJonn)

Coal coke and ditchbulb paste are no longer crushed into coal dust (#722) (LobsterJonn)

Fixed the lavender dye recipe being unobtainable because brown dye claimed its pattern (#731) (LobsterJonn)

Removed the duplicate green dye recipe (#126) (LobsterJonn)

Fixed the affix template recipes that start from a brass plate (#670) (LobsterJonn)

Fixed several item tags (#105, #683, #437) (LobsterJonn)

Unified the crop tags (LobsterJonn)

Ancient Great Ball of Fire now uses its own Ancient lid in the Pressure Chamber as it should (LobsterJonn)

PneumaticCraft assembly now cuts apricorn bits with the drill (LobsterJonn)

Added a Mekanism sawmill recipe turning stripped apricorn logs into apricorn ball lids (LobsterJonn)

Added tooltips to the Cobblemon regional foods explaining that you crouch to eat them yourself (LobsterJonn)

Radical Red gym leaders now roam instead of only staying put in their gyms (LobsterJonn)

Added more structures to the Overlapless unskippable list so they stop being skipped (LobsterJonn)

Hid structures the pack does not generate from Explorer's Compass (LobsterJonn)

Hid biomes the pack does not generate from Nature's Compass (LobsterJonn)

Swapped the Rising Badge with the Earth Badge (LobsterJonn)

Adjusted Joey's team level to match the level cap (LobsterJonn)

Removed unused custom items (LobsterJonn)

The Hall of Origin quest now triggers on entering the dimension rather than the structure (LobsterJonn)

Corrected the catch rates listed in the ATM ball quest (LobsterJonn)

Fixed the Radical Red gym leader quest text (LobsterJonn)

Removed placeholder text from quests (LobsterJonn)

Quest text fixes (LobsterJonn)

Made the recipe check ignore Apotheosis (#707) (DivineFinal)

Prepared for Enamorus' addition to Legendary Monuments (#732) (DivineFinal)

S'nore quest changes (#712) (DivineFinal)

Disabled the new silver ore from Mekanism: More Machine (#729) (item4)

Explicitly marked the Glyph of Nullify Defense as disabled (#740) (item4)

Protected the Robit from Amber Bees and Ars Containment Jars (#723) (item4)

Updated the Artifacts quest (#710) (PrincessStellar)

Updated PT_BR localization (#706, #710, #721) (PrincessStellar)

Neoforge Version is21.1.249

ALWAYS REMEMBER TO BACKUP BEFORE UPDATING

## 8572588

[Detailed changelog](https://github.com/AllTheMods/All-the-Mons/blob/main/CHANGELOG.md)

Changelog

1.2.0 addsPika Power, a new Cobblemon-integrated power block, and rounds out gym badges for theBDSP (Sinnoh)andRadical Red (Kanto)series - both the badges and their badge boxes now drop from gym leaders. It also makes every Cobblemon medicine brewable in a brewing stand, brings a large batch of quest updates.

Pack changes

Added Pika Power (LobsterJonn)

Added badge drops from the BDSP (Sinnoh) and Radical Red (Kanto) gym leaders (LobsterJonn)

Made each series' first gym leader also drop that series' badge box (LobsterJonn)

Added Joey to the ATM trainer series (LobsterJonn)

Added the Helpful Badge (LobsterJonn)

Increased the ATM Badge Box to 12 slots (LobsterJonn)

Occultism tallow now drops from the Pokémon that replaced cows, sheep, pigs, horses, and donkeys when killed with a butcher knife (LobsterJonn)

Added the /allthemons fix_tethers command to free Pokémon left permanently un-pastureable by a lost pasture (LobsterJonn)

Made the Soul-Heart Mechanism block show up in JEI (LobsterJonn)

Hid the unobtainable Meltan Box and Meltan Candy from JEI (LobsterJonn)

Hid the unobtainable badge boxes from JEI (LobsterJonn)

Disabled the Silent Gear guide book given on first world join (LobsterJonn)

Fixed a server crash caused by Legendary Monuments' Ingredient mixin firing on the Nature's Aura altar (LobsterJonn)

Made all Cobblemon medicines brewable in a brewing stand and the Industrial Foregoing Potion Brewer (#680) (NillieZilla)

Made Cobblemon apricorn and saccharine logs and wood strippable with an axe, and enabled ModernFix's beta optimizations (#689) (Uncandango)

Cross-ported Create Infuser balance changes from All the Mods 10 (#702) (item4)

Removed Ancient Origin Balls from the Red Chain tooltip (#703) (DivineFinal)

Fixed the Mekanism rebalance tooltips (#695) (DivineFinal)

Reworked a large batch of Legendary quests (DivineFinal)

Rewrote the Paradox Pokémon quests (DivineFinal)

Clarified the Ultra Beast and Paradox quests (#700) (DivineFinal)

Edited some Legendary Monuments legendary descriptions (#699) (joeychin01)

Backported Apotheosis quests from All the Mods 11 (DivineFinal)

Added a Shield of Retaliation quest (#693) (DivineFinal)

Changed the Mob Imprisonment Tool quest (DivineFinal)

Updated the Pika Star quests (DivineFinal)

Updated the Hostile Neural Networks quests for 6.5.0 (DivineFinal)

Buffed Scylla and Clawdian and added Orb rewards to the Cataclysm quests (#677) (DivineFinal)

Resolved conflicting Oritech Foundry recipes and added an alternate Tainted Refinery recipe (#671, #672) (DivineFinal)

Labelled the Radical Red, Unbound, and Content Creators series as optional (DivineFinal)

Removed missing mods and Variants & Ventures mobs from quest text (DivineFinal)

Replaced the rainbow text in the ATM Star chapter (DivineFinal)

Added more building tips (DivineFinal)

Restored the intended Oritech settings with new TOML configs (#676) (item4)

Added an EnderIO quest (PrincessStellar)

Updated PT_BR localization (PrincessStellar)

Neoforge Version is21.1.248

ALWAYS REMEMBER TO BACKUP BEFORE UPDATING
